# SingleCellStudio Professional - Installation Guide

**Complete single-cell RNA-seq analysis platform with integrated trajectory analysis**

## Quick Installation

### Prerequisites
- **Python 3.8+** (Python 3.10 recommended)
- **Conda** (Miniconda or Anaconda)
- **8GB+ RAM** (16GB+ recommended for large datasets)

### 1. Create Conda Environment
```bash
# Create environment with Python 3.10
conda create -n singlecellstudio python=3.10 -y

# Activate environment
conda activate singlecellstudio
```

### 2. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Alternative: Install core packages manually
pip install numpy pandas matplotlib seaborn
pip install scanpy anndata>=0.8.0
pip install umap-learn leidenalg python-igraph
pip install PySide6 h5py tables
```

### 3. Launch Application
```bash
# Method 1: Use the launcher script (recommended)
./launch.sh

# Method 2: Direct launch
python singlecellstudio.py

# Method 3: From source
python src/main.py
```

## Detailed Installation

### System Requirements

#### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **RAM**: 8GB (16GB+ recommended for datasets >50k cells)
- **Storage**: 2GB free space + 2x dataset size for intermediate files
- **Python**: 3.8+ (3.10 recommended for best compatibility)

#### Recommended Specifications
- **RAM**: 32GB+ for large datasets (>100k cells)
- **CPU**: Multi-core processor (4+ cores recommended)
- **Storage**: SSD for faster I/O operations
- **Display**: 1920x1080+ resolution for optimal interface experience

### Platform-Specific Instructions

#### Windows
```bash
# Install Miniconda (if not already installed)
# Download from: https://docs.conda.io/en/latest/miniconda.html

# Open Anaconda Prompt or PowerShell
conda create -n singlecellstudio python=3.10 -y
conda activate singlecellstudio
pip install -r requirements.txt

# Launch application
python singlecellstudio.py
```

#### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Miniconda
brew install miniconda

# Create environment
conda create -n singlecellstudio python=3.10 -y
conda activate singlecellstudio
pip install -r requirements.txt

# Launch application
python singlecellstudio.py
```

#### Linux (Ubuntu/Debian)
```bash
# Install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Create environment
conda create -n singlecellstudio python=3.10 -y
conda activate singlecellstudio
pip install -r requirements.txt

# Launch application
python singlecellstudio.py
```

### Dependency Details

#### Core Dependencies
```txt
# Data manipulation and analysis
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0

# Single-cell analysis
scanpy>=1.9.0
anndata>=0.8.0

# Visualization
matplotlib>=3.5.0
seaborn>=0.11.0

# Clustering and dimensionality reduction
umap-learn>=0.5.0
leidenalg>=0.8.0
python-igraph>=0.9.0

# GUI framework
PySide6>=6.0.0

# Data I/O
h5py>=3.0.0
tables>=3.6.0
```

#### Optional Dependencies
```txt
# Development and testing
pytest>=7.1.0
pytest-qt>=4.1.0
black>=22.6.0

# Performance optimization
numba>=0.56.0
```

### Verification

#### Test Installation
```bash
# Activate environment
conda activate singlecellstudio

# Check Python version
python --version  # Should be 3.8+

# Test imports
python -c "import scanpy, anndata, PySide6; print('✓ All imports successful')"

# Launch application
python singlecellstudio.py
```

#### Expected Output
```
🔬 SingleCellStudio Professional Edition
==================================================
INFO:main:Starting SingleCellStudio 0.2.0-dev
INFO:main:Professional main window created and shown

Features Available:
- ✅ Data Import and QC
- ✅ Clustering Analysis  
- ✅ Cell Type Annotation
- ✅ Trajectory Analysis (Pseudotime, RNA Velocity, Lineage Tracing)
- ✅ Publication-Quality Visualizations
```

### Troubleshooting

#### Common Issues

**1. PySide6 Installation Issues**
```bash
# Try alternative installation methods
conda install pyside6 -c conda-forge
# or
pip install PySide6 --force-reinstall
```

**2. Scanpy Installation Issues**
```bash
# Install from conda-forge
conda install scanpy -c conda-forge
# or
pip install scanpy --no-deps
pip install numpy pandas matplotlib seaborn
```

**3. Import Errors**
```bash
# Check environment activation
conda activate singlecellstudio
which python  # Should point to conda environment

# Reinstall problematic packages
pip uninstall [package_name]
pip install [package_name]
```

**4. Memory Issues**
```bash
# Check available memory
python -c "import psutil; print(f'Available RAM: {psutil.virtual_memory().available/1024**3:.1f}GB')"

# Increase virtual memory (Windows)
# System Properties > Advanced > Performance > Settings > Advanced > Virtual Memory
```

**5. Display Issues (Linux)**
```bash
# Install X11 libraries
sudo apt-get install python3-pyside6.qtwidgets

# For WSL users
export DISPLAY=:0
```

#### Environment Issues

**Reset Environment**
```bash
# Remove existing environment
conda deactivate
conda env remove -n singlecellstudio

# Create fresh environment
conda create -n singlecellstudio python=3.10 -y
conda activate singlecellstudio
pip install -r requirements.txt
```

**Check Environment**
```bash
# List installed packages
conda list

# Check for conflicts
conda info
pip check
```

### Development Installation

For developers who want to modify the source code:

```bash
# Clone repository
git clone <repository-url>
cd SingleCellStudio

# Create development environment
conda create -n singlecellstudio-dev python=3.10 -y
conda activate singlecellstudio-dev

# Install in development mode
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

### Docker Installation (Advanced)

For containerized deployment:

```dockerfile
FROM continuumio/miniconda3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxrender1 \
    libxext6 \
    libsm6 \
    libice6

# Create environment
COPY requirements.txt /tmp/
RUN conda create -n singlecellstudio python=3.10 -y
RUN conda run -n singlecellstudio pip install -r /tmp/requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Set entry point
CMD ["conda", "run", "-n", "singlecellstudio", "python", "singlecellstudio.py"]
```

### Performance Optimization

#### Memory Optimization
```bash
# Set environment variables for better memory usage
export NUMBA_CACHE_DIR=/tmp/numba_cache
export SCANPY_CACHE_DIR=/tmp/scanpy_cache
```

#### Parallel Processing
```bash
# Set number of threads for parallel operations
export OMP_NUM_THREADS=4
export NUMBA_NUM_THREADS=4
```

### Support

If you encounter issues not covered in this guide:

1. **Check Log Files**: Review `singlecellstudio.log` for detailed error messages
2. **Verify Dependencies**: Ensure all required packages are installed
3. **System Resources**: Monitor memory and CPU usage during analysis
4. **Environment**: Confirm conda environment is properly activated

For additional support, please refer to the documentation in the `docs/` directory or contact the development team. 