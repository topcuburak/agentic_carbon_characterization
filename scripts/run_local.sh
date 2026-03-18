#!/bin/bash
# ─── Agentic AI Benchmark Runner (No PBS) ───────────────────────────────────
# Run directly on any machine with GPUs. No scheduler required.
#
# Usage:
#   bash scripts/run_local.sh                    # full experiment
#   bash scripts/run_local.sh --quick            # quick test (1 task, 1 rep)
#   bash scripts/run_local.sh --model llama-8b   # single model only
#   bash scripts/run_local.sh --model qwen-0.8b  # single model only
# ─────────────────────────────────────────────────────────────────────────────

set -e

PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT"

# ─── Defaults ────────────────────────────────────────────────────────────────

REPS=3
OUTPUT_DIR="$PROJECT/results"
MODELS="both"
QUICK=false
PORT=8000
FRAMEWORKS=""  # empty = all frameworks

# ─── Parse args ──────────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)       QUICK=true; shift ;;
        --model)       MODELS="$2"; shift 2 ;;
        --reps)        REPS="$2"; shift 2 ;;
        --port)        PORT="$2"; shift 2 ;;
        --output-dir)  OUTPUT_DIR="$2"; shift 2 ;;
        --frameworks)  FRAMEWORKS="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: bash scripts/run_local.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick              Quick test (1 task, 1 rep, mock only)"
            echo "  --model MODEL        Run single model: llama-8b or qwen-0.8b (default: both)"
            echo "  --reps N             Number of repetitions (default: 3)"
            echo "  --port PORT          vLLM server port (default: 8000)"
            echo "  --output-dir DIR     Output directory (default: ./results)"
            echo "  --frameworks LIST    Comma-separated frameworks (default: all)"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if $QUICK; then
    REPS=1
    TASK_ARGS="--task-ids mhqa_01 cgen_01"
    FRAMEWORKS="langgraph"
    echo "=== QUICK TEST MODE ==="
else
    TASK_ARGS=""
fi

FRAMEWORK_ARGS=""
if [ -n "$FRAMEWORKS" ]; then
    FRAMEWORK_ARGS="--frameworks $FRAMEWORKS"
fi

export VLLM_BASE_URL="http://localhost:$PORT/v1"
export VLLM_API_KEY="EMPTY"

# ─── Helper functions ────────────────────────────────────────────────────────

VLLM_PID=""

start_vllm() {
    local model_hf=$1
    local tp=$2

    echo ""
    echo "=== Starting vLLM: $model_hf (TP=$tp) on port $PORT ==="
    python -m vllm.entrypoints.openai.api_server \
        --model "$model_hf" \
        --tensor-parallel-size "$tp" \
        --port "$PORT" \
        --api-key "EMPTY" \
        --max-model-len 8192 \
        --enable-auto-tool-choice \
        --tool-call-parser hermes &
    VLLM_PID=$!

    echo "Waiting for vLLM (PID=$VLLM_PID) to be ready..."
    for i in $(seq 1 60); do
        if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
            echo "vLLM ready after ~$((i * 5)) seconds."
            return 0
        fi
        sleep 5
    done
    echo "ERROR: vLLM did not start within 5 minutes."
    kill $VLLM_PID 2>/dev/null
    exit 1
}

stop_vllm() {
    if [ -n "$VLLM_PID" ]; then
        echo "Stopping vLLM (PID=$VLLM_PID)..."
        kill $VLLM_PID 2>/dev/null
        wait $VLLM_PID 2>/dev/null || true
        VLLM_PID=""
    fi
}

# Clean up on exit
trap stop_vllm EXIT

run_model() {
    local model_key=$1
    local model_hf=$2
    local tp=$3

    echo ""
    echo "=========================================="
    echo "  MODEL: $model_hf"
    echo "=========================================="

    start_vllm "$model_hf" "$tp"

    python runner.py \
        --models "$model_key" \
        $FRAMEWORK_ARGS \
        $TASK_ARGS \
        --reps "$REPS" \
        --output-dir "$OUTPUT_DIR"

    stop_vllm
}

# ─── Run experiments ─────────────────────────────────────────────────────────

echo "=========================================="
echo "  Agentic AI Benchmark (no PBS)"
echo "  Reps: $REPS"
echo "  Models: $MODELS"
echo "  Output: $OUTPUT_DIR"
echo "  Started: $(date)"
echo "=========================================="

case $MODELS in
    llama-8b)
        run_model "llama-8b" "meta-llama/Llama-3.1-8B-Instruct" 1
        ;;
    qwen-0.8b)
        run_model "qwen-0.8b" "Qwen/Qwen3.5-0.8B" 1
        ;;
    both)
        run_model "llama-8b" "meta-llama/Llama-3.1-8B-Instruct" 1
        run_model "qwen-0.8b" "Qwen/Qwen3.5-0.8B" 1
        ;;
    *)
        echo "Unknown model: $MODELS (use llama-8b, qwen-0.8b, or both)"
        exit 1
        ;;
esac

# ─── Generate plots ─────────────────────────────────────────────────────────

echo ""
echo "=== Generating analysis plots ==="
python -m analysis.plots --results-dir "$OUTPUT_DIR" || echo "Plot generation failed (non-fatal)"

echo ""
echo "=========================================="
echo "  ALL EXPERIMENTS COMPLETE"
echo "  Results: $OUTPUT_DIR"
echo "  Finished: $(date)"
echo "=========================================="
