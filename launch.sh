#!/bin/bash

# SingleCellStudio Professional Launch Script
# This script activates the conda environment and launches the application

echo "🔬 SingleCellStudio Professional Edition"
echo "========================================"

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda is not installed or not in PATH"
    echo "Please install Miniconda or Anaconda first"
    exit 1
fi

# Check if environment exists
if ! conda env list | grep -q "singlecellstudio"; then
    echo "❌ Error: singlecellstudio environment not found"
    echo "Please run the installation steps first:"
    echo "conda create -n singlecellstudio python=3.10 -y"
    echo "conda activate singlecellstudio"
    echo "pip install -r requirements.txt"
    exit 1
fi

echo "🚀 Activating singlecellstudio environment..."

# Activate conda environment and launch application
eval "$(conda shell.bash hook)"
conda activate singlecellstudio

echo "🎯 Launching SingleCellStudio Professional..."
python singlecellstudio.py

echo "👋 SingleCellStudio Professional closed" 