# SingleCellStudio Data Loading Guide

## 🚀 Overview

SingleCellStudio now supports comprehensive data loading for single cell RNA-seq datasets! This guide shows you how to import your data and get started with analysis.

## 📁 Supported Data Formats

### 1. 10X Genomics MTX Format (Recommended)
**Folder containing:**
- `matrix.mtx.gz` - Gene expression matrix (Market Matrix format)
- `barcodes.tsv.gz` - Cell barcodes (one per line)
- `features.tsv.gz` - Gene information (ID, symbol, type)

**Alternative file names supported:**
- Uncompressed versions (`.mtx`, `.tsv`)
- Legacy format with `genes.tsv.gz` instead of `features.tsv.gz`

### 2. 10X Genomics HDF5 Format
**Single file:**
- `filtered_feature_bc_matrix.h5` - Complete dataset in HDF5 format
- Contains matrix, barcodes, and features in structured format

### 3. AnnData H5AD Format
**Single file:**
- `data.h5ad` - AnnData format (scanpy/pandas compatible)
- Preserves all metadata, annotations, and analysis results

### 4. CSV/TSV Format
**Single file:**
- `data.csv` or `data.tsv` - Tabular format
- Genes as columns, cells as rows (or vice versa)
- Supports gzipped files (`.csv.gz`, `.tsv.gz`)

## 🖥️ How to Load Data

### Method 1: GUI Interface
1. Launch SingleCellStudio: `python src/main.py`
2. Click **"Import Data"** button or use `File → Import Data` (Ctrl+I)
3. Browse and select your data file/folder
4. Review data information and validation results
5. Click **"Import"** to load into workspace

### Method 2: Command Line Testing
```bash
# Test data loading from command line
python examples/test_data_loading.py /path/to/your/data

# Examples:
python examples/test_data_loading.py /path/to/filtered_feature_bc_matrix/
python examples/test_data_loading.py /path/to/filtered_feature_bc_matrix.h5
python examples/test_data_loading.py /path/to/data.h5ad
```

### Method 3: Python API
```python
from src.data import DataLoader, get_data_info

# Get data information without loading
info = get_data_info("/path/to/data")
print(f"Format: {info['format']}")
print(f"Cells: {info.get('n_cells', 'Unknown')}")
print(f"Genes: {info.get('n_genes', 'Unknown')}")

# Load data
loader = DataLoader()
adata = loader.load("/path/to/data")

print(f"Loaded: {adata.n_obs} cells × {adata.n_vars} genes")
```

## 🔍 Data Validation

SingleCellStudio automatically validates your data and provides:

### ✅ Quality Checks
- **Structure validation**: Ensures data integrity
- **Dimension validation**: Checks cell/gene counts
- **Data type validation**: Verifies numeric data
- **Identifier validation**: Checks gene names and cell barcodes
- **Quality metrics**: Sparsity, expression levels, empty cells/genes

### ⚠️ Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Duplicate gene names | Use `adata.var_names_unique()` |
| Empty cells/genes | Filter using scanpy: `sc.pp.filter_cells()`, `sc.pp.filter_genes()` |
| Very large files | Consider using sparse format or subsampling |
| Memory issues | Load data in chunks or use HDF5 format |

## 📊 Example Workflows

### Loading 10X Data
```python
# Your data structure:
# filtered_feature_bc_matrix/
# ├── matrix.mtx.gz
# ├── barcodes.tsv.gz
# └── features.tsv.gz

from src.data import DataLoader

loader = DataLoader()
adata = loader.load("filtered_feature_bc_matrix/")

print(f"Dataset: {adata.n_obs} cells × {adata.n_vars} genes")
print(f"Sparsity: {(adata.X == 0).sum() / adata.X.size:.1%}")
```

### Loading H5 Data
```python
# Single H5 file
adata = loader.load("filtered_feature_bc_matrix.h5")

# Check metadata
print("Gene metadata columns:", list(adata.var.columns))
print("Cell metadata columns:", list(adata.obs.columns))
```

### Data Quality Assessment
```python
from src.data.validators import DataValidator

validator = DataValidator()
results = validator.validate_adata(adata)

print(f"Validation: {'✅ Passed' if results['valid'] else '❌ Failed'}")
print(f"Errors: {len(results['errors'])}")
print(f"Warnings: {len(results['warnings'])}")

# Show recommendations
for rec in results['recommendations']:
    print(f"💡 {rec}")
```

## 🧬 Data Structure

After loading, your data is stored in an **AnnData object** with:

```python
adata.X          # Expression matrix (cells × genes)
adata.obs        # Cell metadata (DataFrame)
adata.var        # Gene metadata (DataFrame)
adata.uns        # Unstructured metadata (dict)
adata.obsm       # Multi-dimensional cell annotations
adata.varm       # Multi-dimensional gene annotations
```

### SingleCellStudio Metadata
```python
# Loading information
adata.uns['scs_metadata']     # Source path, format, load time
adata.uns['scs_validation']   # Validation results
```

## 🚀 Performance Tips

### For Large Datasets (>100K cells)
1. **Use HDF5 format** for faster loading
2. **Enable caching** for repeated access
3. **Consider subsampling** for initial exploration
4. **Use sparse matrices** to save memory

### Memory Optimization
```python
# Convert to sparse if needed
import scipy.sparse as sp
if not sp.issparse(adata.X):
    adata.X = sp.csr_matrix(adata.X)

# Remove unnecessary data
adata.raw = adata  # Save original
adata = adata[:, adata.var.highly_variable]  # Keep only HVGs
```

## 🔧 Troubleshooting

### Common Errors

**"Missing required files"**
- Ensure all 10X files are present and named correctly
- Check file permissions

**"Failed to load data"**
- Verify file format and integrity
- Check available memory for large files
- Try loading a subset first

**"Validation warnings"**
- Review data quality recommendations
- Consider filtering low-quality cells/genes

### Getting Help

1. **Check validation results** for specific recommendations
2. **Review error messages** for technical details
3. **Test with example data** to verify functionality
4. **Use command-line tool** for detailed diagnostics

## 📈 Next Steps

After loading your data:
1. **Explore data structure** and metadata
2. **Apply quality control** filtering
3. **Proceed to analysis** (coming soon!)
4. **Visualize results** (coming soon!)

---

**🎉 Ready to analyze your single cell data!**

The data loading system is now fully functional and ready for production use. The next development phase will focus on analysis pipelines and interactive visualizations. 