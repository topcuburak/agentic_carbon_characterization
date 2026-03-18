#!/bin/bash
# ─── Server Setup Script ─────────────────────────────────────────────────────
# Run this once after cloning the repo to /scratch/$USER/agentic
# Sets up conda environment with all dependencies.
# ──────────────────────────────────────────────────────────────────────────────

set -e

SCRATCH="/scratch/$USER"
PROJECT_DIR="$SCRATCH/agentic"
CONDA_DIR="$SCRATCH/anaconda3"
ENV_NAME="agentic_bench"

echo "=== Setting up agentic AI benchmark environment ==="

# Check conda
if [ ! -d "$CONDA_DIR" ]; then
    echo "Anaconda not found at $CONDA_DIR"
    echo "Install Anaconda first:"
    echo "  wget https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Linux-x86_64.sh"
    echo "  bash Anaconda3-*.sh -b -p $CONDA_DIR"
    exit 1
fi

export PATH="$CONDA_DIR/bin:$CONDA_DIR/condabin:$PATH"

# Create environment
echo "Creating conda environment: $ENV_NAME"
conda create -n $ENV_NAME python=3.11 -y
source activate $ENV_NAME

# Install PyTorch (for GPU support needed by some frameworks)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Install vLLM (for serving models)
pip install vllm

# Install project dependencies
cd $PROJECT_DIR
pip install -r requirements.txt

echo ""
echo "=== Setup complete ==="
echo "Activate with: source activate $ENV_NAME"
echo "Project dir: $PROJECT_DIR"
