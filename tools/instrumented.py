"""
Instrumented tool wrappers that measure CPU time and energy per call.
Wraps each tool function to capture resource usage.
"""

import time
import os
from tools import TOOL_REGISTRY


def _read_rapl_uj() -> tuple[int | None, int | None]:
    """Read CPU and DRAM RAPL energy counters (microjoules)."""
    cpu_uj = None
    dram_uj = None
    try:
        import glob
        for name_path in glob.glob("/sys/class/powercap/intel-rapl:*/name"):
            name = open(name_path).read().strip().lower()
            energy_path = name_path.replace("/name", "/energy_uj")
            if name.startswith("package-") and os.path.exists(energy_path):
                val = int(open(energy_path).read().strip())
                cpu_uj = (cpu_uj or 0) + val
    except Exception:
        pass
    return cpu_uj, dram_uj


def _read_gpu_energy_uj() -> int | None:
    """Read GPU total energy consumption if available."""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        # nvmlDeviceGetTotalEnergyConsumption returns mJ
        mj = pynvml.nvmlDeviceGetTotalEnergyConsumption(handle)
        pynvml.nvmlShutdown()
        return mj * 1000  # mJ -> uJ
    except Exception:
        return None


def call_tool_instrumented(tool_name: str, arguments: dict) -> dict:
    """
    Call a tool with full instrumentation.

    Returns dict with:
        result: str — tool output
        duration_ms: int — wall clock time
        cpu_time_ms: float — CPU user+system time
        gpu_energy_j: float — GPU energy consumed
        cpu_energy_j: float — CPU energy consumed
    """
    func = TOOL_REGISTRY[tool_name]["function"]

    # Snapshot before
    cpu_before = time.process_time()
    wall_before = time.time()
    rapl_before, _ = _read_rapl_uj()
    gpu_before = _read_gpu_energy_uj()

    # Execute tool
    try:
        result = func(**arguments)
    except Exception as e:
        result = f"Error: {e}"

    # Snapshot after
    wall_after = time.time()
    cpu_after = time.process_time()
    rapl_after, _ = _read_rapl_uj()
    gpu_after = _read_gpu_energy_uj()

    # Compute deltas
    duration_ms = int((wall_after - wall_before) * 1000)
    cpu_time_ms = (cpu_after - cpu_before) * 1000

    cpu_energy_j = 0.0
    if rapl_before is not None and rapl_after is not None:
        delta = rapl_after - rapl_before
        if delta < 0:
            delta += 2**32
        cpu_energy_j = delta / 1e6  # uJ -> J

    gpu_energy_j = 0.0
    if gpu_before is not None and gpu_after is not None:
        delta = gpu_after - gpu_before
        if delta < 0:
            delta += 2**32
        gpu_energy_j = delta / 1e6  # uJ -> J

    return {
        "result": str(result),
        "duration_ms": duration_ms,
        "cpu_time_ms": round(cpu_time_ms, 3),
        "gpu_energy_j": round(gpu_energy_j, 6),
        "cpu_energy_j": round(cpu_energy_j, 6),
    }
