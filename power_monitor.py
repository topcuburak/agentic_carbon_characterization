"""
Power monitoring with phase-aware attribution.
Samples CPU (Intel RAPL) and GPU (NVML) power at configurable intervals,
tagging each sample with the current execution phase.
"""

import time
import csv
import os
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from config import POWER_CONFIG, RESULTS_DIR


class Phase(str, Enum):
    """Execution phases within an agentic run."""
    INFERENCE = "inference"
    TOOL_EXECUTION = "tool_execution"
    ORCHESTRATION = "orchestration"
    IDLE = "idle"


@dataclass
class PowerSample:
    """A single power measurement sample."""
    timestamp_ms: int
    phase: str
    gpu_power_w: list[float]
    cpu_pkg_power_w: float | None
    dram_power_w: float | None


@dataclass
class PhaseEnergy:
    """Accumulated energy for a single phase."""
    gpu_energy_j: list[float] = field(default_factory=list)
    cpu_energy_j: float = 0.0
    dram_energy_j: float = 0.0
    duration_ms: int = 0


@dataclass
class PowerReport:
    """Final power/energy report for a complete run."""
    samples: list[PowerSample]
    phase_energy: dict[str, PhaseEnergy]
    total_gpu_energy_j: list[float]
    total_cpu_energy_j: float
    total_dram_energy_j: float
    total_energy_j: float
    total_duration_ms: int


class PowerMonitor:
    """
    Phase-aware power monitor.

    Usage:
        monitor = PowerMonitor(run_id="langgraph_llama8b_task1_rep0")
        monitor.start()

        monitor.set_phase(Phase.ORCHESTRATION)
        # ... framework builds prompt ...
        monitor.set_phase(Phase.INFERENCE)
        # ... LLM call ...
        monitor.set_phase(Phase.TOOL_EXECUTION)
        # ... tool runs ...

        monitor.stop()
        report = monitor.get_report()
    """

    def __init__(self, run_id: str, output_dir: Path | None = None):
        self.run_id = run_id
        self.output_dir = output_dir or RESULTS_DIR / "power_traces"
        self._samples: list[PowerSample] = []
        self._current_phase = Phase.IDLE
        self._phase_lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._start_time: float = 0.0

        # NVML handles (lazy init)
        self._nvml_initialized = False
        self._gpu_handles = []

        # RAPL state
        self._rapl_paths: dict[str, str] = {}
        self._prev_cpu_uj: int | None = None
        self._prev_dram_uj: int | None = None
        self._prev_sample_time: float | None = None

    # ─── NVML (GPU) ──────────────────────────────────────────────────────

    def _init_nvml(self):
        """
        Initialize NVML for GPU power reading.
        Auto-detects which GPUs are visible to this process.

        PBS/SLURM set CUDA_VISIBLE_DEVICES to restrict GPU access.
        NVML sees only the GPUs visible to the process when
        CUDA_VISIBLE_DEVICES is set, so we enumerate all visible devices.
        If CUDA_VISIBLE_DEVICES is not set, we monitor all GPUs on the node.
        """
        if not POWER_CONFIG.use_nvml:
            return
        try:
            import pynvml
            pynvml.nvmlInit()
            self._nvml_initialized = True

            num_gpus = pynvml.nvmlDeviceGetCount()
            self._gpu_indices_actual = []

            # Check if CUDA_VISIBLE_DEVICES is set (PBS/SLURM job)
            import os
            cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")

            if cuda_visible:
                # PBS assigned specific GPUs (e.g., "3,5")
                # NVML still sees ALL GPUs on the node, indexed 0..N-1.
                # CUDA_VISIBLE_DEVICES remaps them for CUDA, but NVML uses
                # physical indices. We need to monitor the physical indices.
                visible_ids = [int(x.strip()) for x in cuda_visible.split(",") if x.strip().isdigit()]
                for idx in visible_ids:
                    if idx < num_gpus:
                        handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
                        self._gpu_handles.append(handle)
                        self._gpu_indices_actual.append(idx)
            else:
                # No restriction — monitor all GPUs
                for idx in range(num_gpus):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
                    self._gpu_handles.append(handle)
                    self._gpu_indices_actual.append(idx)

            if self._gpu_handles:
                gpu_names = []
                for h in self._gpu_handles:
                    name = pynvml.nvmlDeviceGetName(h)
                    if isinstance(name, bytes):
                        name = name.decode()
                    gpu_names.append(name)
                print(f"  Power monitor: tracking GPUs {self._gpu_indices_actual} ({', '.join(gpu_names)})")

        except Exception as e:
            self._nvml_initialized = False
            self._gpu_handles = []
            self._gpu_indices_actual = []

    def _read_gpu_power(self) -> list[float]:
        """Read current GPU power draw in watts."""
        if not self._nvml_initialized:
            return [0.0] * max(len(self._gpu_handles), 1)
        try:
            import pynvml
            powers = []
            for handle in self._gpu_handles:
                mw = pynvml.nvmlDeviceGetPowerUsage(handle)
                powers.append(mw / 1000.0)  # mW -> W
            return powers
        except Exception:
            return [0.0] * len(self._gpu_handles)

    def _shutdown_nvml(self):
        """Shutdown NVML."""
        if self._nvml_initialized:
            try:
                import pynvml
                pynvml.nvmlShutdown()
            except Exception:
                pass
            self._nvml_initialized = False

    # ─── RAPL (CPU/DRAM) ─────────────────────────────────────────────────

    def _init_rapl(self):
        """
        Discover RAPL energy counters.
        Searches multiple powercap paths (default /sys/class/powercap,
        custom server paths like /scratch2/<user>-logs/powercap, or
        RAPL_POWERCAP_PATH env var).
        Aggregates all CPU packages (multi-socket) into a single reading.
        """
        if not POWER_CONFIG.use_rapl:
            return
        import glob as globmod

        # Find the first powercap base that contains intel-rapl
        rapl_base = None
        for search_path in POWER_CONFIG.rapl_search_paths:
            if not search_path:
                continue
            candidate = os.path.join(search_path, "intel-rapl")
            if os.path.isdir(candidate):
                rapl_base = candidate
                break

        if rapl_base is None:
            return

        # Discover all CPU packages and DRAM domains
        self._rapl_cpu_paths = []  # List of paths for multi-socket aggregation
        for name_path in globmod.glob(os.path.join(rapl_base, "intel-rapl:*", "name")):
            try:
                name = open(name_path).read().strip().lower()
                energy_path = name_path.replace("/name", "/energy_uj")
                if os.path.exists(energy_path):
                    if name.startswith("package-"):
                        self._rapl_cpu_paths.append(energy_path)
                    elif "dram" in name:
                        self._rapl_paths["dram"] = energy_path
            except Exception:
                continue

        # Check sub-domains for DRAM and core
        for name_path in globmod.glob(os.path.join(rapl_base, "intel-rapl:*", "intel-rapl:*:*", "name")):
            try:
                name = open(name_path).read().strip().lower()
                energy_path = name_path.replace("/name", "/energy_uj")
                if os.path.exists(energy_path):
                    if "dram" in name:
                        self._rapl_paths["dram"] = energy_path
            except Exception:
                continue

        # Store combined package path info
        if self._rapl_cpu_paths:
            self._rapl_paths["cpu"] = "multi"  # Sentinel: use _rapl_cpu_paths
            print(f"  Power monitor: RAPL found at {rapl_base} ({len(self._rapl_cpu_paths)} CPU package(s))")

    def _read_rapl_uj(self, domain: str) -> int | None:
        """Read RAPL energy counter in microjoules.
        For CPU, aggregates across all packages (multi-socket).
        """
        if domain == "cpu" and hasattr(self, "_rapl_cpu_paths") and self._rapl_cpu_paths:
            try:
                total = 0
                for path in self._rapl_cpu_paths:
                    with open(path, "r") as f:
                        total += int(f.read().strip())
                return total
            except Exception:
                return None

        path = self._rapl_paths.get(domain)
        if path is None or path == "multi":
            return None
        try:
            with open(path, "r") as f:
                return int(f.read().strip())
        except Exception:
            return None

    # ─── Sampling Loop ───────────────────────────────────────────────────

    def _sample_loop(self):
        """Background thread: sample power at configured interval."""
        interval_s = POWER_CONFIG.sampling_interval_ms / 1000.0

        while self._running:
            now = time.time()
            elapsed_ms = int((now - self._start_time) * 1000)

            with self._phase_lock:
                phase = self._current_phase

            # GPU power (instantaneous)
            gpu_w = self._read_gpu_power()

            # CPU/DRAM power (delta-based)
            cpu_uj = self._read_rapl_uj("cpu")
            dram_uj = self._read_rapl_uj("dram")

            cpu_w = None
            dram_w = None

            if self._prev_sample_time is not None:
                dt = now - self._prev_sample_time
                if dt > 0:
                    if cpu_uj is not None and self._prev_cpu_uj is not None:
                        delta_cpu = cpu_uj - self._prev_cpu_uj
                        if delta_cpu < 0:  # Counter wrapped
                            delta_cpu += 2**32
                        cpu_w = (delta_cpu / 1e6) / dt

                    if dram_uj is not None and self._prev_dram_uj is not None:
                        delta_dram = dram_uj - self._prev_dram_uj
                        if delta_dram < 0:
                            delta_dram += 2**32
                        dram_w = (delta_dram / 1e6) / dt

            self._prev_sample_time = now
            self._prev_cpu_uj = cpu_uj
            self._prev_dram_uj = dram_uj

            sample = PowerSample(
                timestamp_ms=elapsed_ms,
                phase=phase.value,
                gpu_power_w=gpu_w,
                cpu_pkg_power_w=cpu_w,
                dram_power_w=dram_w,
            )
            self._samples.append(sample)

            time.sleep(interval_s)

    # ─── Public API ──────────────────────────────────────────────────────

    def start(self):
        """Start power monitoring in a background thread."""
        self._init_nvml()
        self._init_rapl()

        self._samples = []
        self._running = True
        self._start_time = time.time()
        self._prev_sample_time = None
        self._prev_cpu_uj = None
        self._prev_dram_uj = None

        self._thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop power monitoring and finalize."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self._shutdown_nvml()

    def set_phase(self, phase: Phase):
        """Set the current execution phase (thread-safe)."""
        with self._phase_lock:
            self._current_phase = phase

    def get_report(self) -> PowerReport:
        """Compute the final power/energy report from collected samples."""
        num_gpus = len(self._gpu_handles) or 1
        interval_s = POWER_CONFIG.sampling_interval_ms / 1000.0

        # Accumulate energy per phase
        phase_energy: dict[str, PhaseEnergy] = {}
        for phase in Phase:
            pe = PhaseEnergy()
            pe.gpu_energy_j = [0.0] * num_gpus
            phase_energy[phase.value] = pe

        for sample in self._samples:
            pe = phase_energy[sample.phase]
            pe.duration_ms += POWER_CONFIG.sampling_interval_ms

            for i, gw in enumerate(sample.gpu_power_w):
                if i < len(pe.gpu_energy_j):
                    pe.gpu_energy_j[i] += gw * interval_s

            if sample.cpu_pkg_power_w is not None:
                pe.cpu_energy_j += sample.cpu_pkg_power_w * interval_s

            if sample.dram_power_w is not None:
                pe.dram_energy_j += sample.dram_power_w * interval_s

        # Totals
        total_gpu_j = [0.0] * num_gpus
        total_cpu_j = 0.0
        total_dram_j = 0.0
        total_duration = 0

        for pe in phase_energy.values():
            for i in range(num_gpus):
                if i < len(pe.gpu_energy_j):
                    total_gpu_j[i] += pe.gpu_energy_j[i]
            total_cpu_j += pe.cpu_energy_j
            total_dram_j += pe.dram_energy_j
            total_duration += pe.duration_ms

        total_energy = sum(total_gpu_j) + total_cpu_j + total_dram_j

        return PowerReport(
            samples=self._samples,
            phase_energy=phase_energy,
            total_gpu_energy_j=total_gpu_j,
            total_cpu_energy_j=total_cpu_j,
            total_dram_energy_j=total_dram_j,
            total_energy_j=total_energy,
            total_duration_ms=total_duration,
        )

    def save_trace(self, report: PowerReport | None = None) -> Path:
        """Save the power trace to a CSV file."""
        if report is None:
            report = self.get_report()

        os.makedirs(self.output_dir, exist_ok=True)
        csv_path = self.output_dir / f"{self.run_id}_power_trace.csv"

        gpu_indices = getattr(self, "_gpu_indices_actual", []) or list(range(len(self._gpu_handles)))
        gpu_headers = [f"gpu{i}_power_w" for i in gpu_indices]

        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_ms", "phase", *gpu_headers, "cpu_pkg_power_w", "dram_power_w"])
            for s in report.samples:
                writer.writerow([
                    s.timestamp_ms,
                    s.phase,
                    *[round(g, 2) for g in s.gpu_power_w],
                    round(s.cpu_pkg_power_w, 2) if s.cpu_pkg_power_w is not None else "",
                    round(s.dram_power_w, 2) if s.dram_power_w is not None else "",
                ])

        return csv_path
