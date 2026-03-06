# SingleCellStudio Installation & Usage Guide

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (recommended: Python 3.9 or 3.10)
- **Conda** or **Miniconda** installed
- **Linux/WSL** environment (tested on Ubuntu)

## 📦 Installation Steps

### Step 1: Create Conda Environment
```bash
# Create a new conda environment
conda create -n singlecellstudio python=3.10 -y

# Activate the environment
conda activate singlecellstudio
```

### Step 2: Install Core Dependencies
```bash
# Install scientific computing packages
conda install -c conda-forge numpy pandas matplotlib seaborn -y

# Install scanpy and single-cell analysis tools
conda install -c conda-forge scanpy -y

# Install PySide6 for GUI
conda install -c conda-forge pyside6 -y

# Install additional packages
pip install anndata>=0.8.0 umap-learn leidenalg
```

### Step 3: Clone/Download SingleCellStudio
```bash
# If you have git
git clone <repository-url>
cd SingleCellStudio

# Or download and extract the folder, then navigate to it
cd path/to/SingleCellStudio
```

### Step 4: Download Sample Data (Optional)
```bash
# Download sample data for testing
cd examples
python download_sample_data.py
cd ..
```

## 🎯 Running SingleCellStudio

### Method 1: Direct Launch (Recommended)
```bash
# Make sure you're in the SingleCellStudio directory
cd SingleCellStudio

# Activate conda environment
conda activate singlecellstudio

# Launch the application
python src/main.py
```

### Method 2: From Any Directory
```bash
# Activate environment
conda activate singlecellstudio

# Run from anywhere (adjust path as needed)
python /path/to/SingleCellStudio/src/main.py
```

## 📊 Using SingleCellStudio

### 1. **Launch Application**
- Run the command above
- Main window will open with "Import Data" button

### 2. **Import Your Data**
- Click "Import Data" button
- **Tab 1 - File Selection**: Choose your data file
  - Supported formats: 10X MTX folders, 10X H5 files, H5AD files, CSV/TSV
- **Tab 2 - Data Preview**: Review your data structure
- **Tab 3 - Validation**: Check data quality
- Click "Import" to proceed

### 3. **Run Analysis**
- Analysis window opens automatically after import
- Click "Run Analysis" to start the standard pipeline
- Progress bar shows real-time updates
- Analysis includes: QC → Filtering → Normalization → PCA → UMAP → Clustering

### 4. **Explore Results**
- **Overview Tab**: Analysis summary and statistics
- **Data Tab**: Processed data information
- **Plots Tab**: Generate visualizations
  - UMAP plots with cluster coloring
  - PCA plots with variance explained
  - Quality control plots
  - Cluster analysis plots
  - Gene expression heatmaps
  - Violin plots for gene expression

### 5. **Results Location**
All results are automatically saved in:
```
results_[filename]_[timestamp]/
├── intermediate_data/
│   ├── normalize_data.h5ad      # After normalization
│   └── clustering.h5ad          # Final analysis
├── metadata/                    # CSV files with metrics
├── plots/                       # All generated plots (PNG/PDF/SVG)
└── logs/                        # Execution logs
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. **PySide6 Import Error**
```bash
# Try alternative PySide6 installation
conda install -c anaconda pyside6 -y
# or
pip install PySide6
```

#### 2. **Scanpy Import Error**
```bash
# Reinstall scanpy
conda uninstall scanpy -y
pip install scanpy
```

#### 3. **UMAP/Leiden Import Error**
```bash
# Install missing packages
pip install umap-learn leidenalg python-igraph
```

#### 4. **Memory Issues with Large Datasets**
- Close other applications
- Use smaller subset of data for testing
- Consider using a machine with more RAM (>8GB recommended)

#### 5. **GUI Not Displaying**
```bash
# For WSL users, ensure X11 forwarding is enabled
export DISPLAY=:0
# or install VcXsrv on Windows
```

## 📋 System Requirements

### Minimum Requirements
- **RAM**: 8GB (16GB+ recommended for large datasets)
- **Storage**: 2GB free space (more for large datasets)
- **CPU**: Multi-core processor recommended

### Tested Environments
- **Ubuntu 20.04/22.04** (WSL and native)
- **Python 3.9/3.10**
- **Conda 4.12+**

## 🧪 Test Installation

### Quick Test with Sample Data
```bash
# Activate environment
conda activate singlecellstudio

# Navigate to SingleCellStudio
cd SingleCellStudio

# Download sample data
cd examples
python download_sample_data.py

# Launch application
cd ..
python src/main.py

# In GUI: Import examples/sample_data/filtered_feature_bc_matrix.h5
# Run analysis and generate plots
```

## 📖 Data Format Guide

### Supported Input Formats

1. **10X Genomics MTX Format** (folder with 3 files):
   - `matrix.mtx.gz` - Gene expression matrix
   - `barcodes.tsv.gz` - Cell barcodes
   - `features.tsv.gz` - Gene information

2. **10X Genomics H5 Format**:
   - `filtered_feature_bc_matrix.h5` - HDF5 format

3. **AnnData H5AD Format**:
   - `data.h5ad` - Processed single-cell data

4. **CSV/TSV Format**:
   - Genes as rows, cells as columns
   - Supports compression (.gz)

## 🆘 Getting Help

### Log Files
Check execution logs in the results folder:
```
results_[filename]_[timestamp]/logs/execution_log.txt
```

### Debug Mode
Run with debug output:
```bash
python src/main.py --debug
```

### Common Data Issues
- **Duplicate gene names**: Automatically handled with suffix numbering
- **Large file loading**: Use progress bars to monitor
- **Memory usage**: Monitor system resources during analysis

## 🔄 Environment Management

### Deactivate Environment
```bash
conda deactivate
```

### Remove Environment (if needed)
```bash
conda env remove -n singlecellstudio
```

### Update Dependencies
```bash
conda activate singlecellstudio
conda update --all
pip install --upgrade scanpy anndata
```

---

## 🎉 You're Ready!

Your SingleCellStudio installation is complete! Start with the sample data to familiarize yourself with the interface, then import your own single-cell datasets for analysis.

For advanced usage and development information, see:
- `DEVELOPMENT_LOG.md` - Technical development details
- `DATA_LOADING_GUIDE.md` - Advanced data loading options
- `examples/` - Example scripts and data 