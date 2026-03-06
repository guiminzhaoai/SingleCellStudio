"""
SingleCellStudio Data Package

This package handles all data import, validation, and format conversion
for single cell RNA-seq datasets.

Supported formats:
- 10X Genomics (MTX + TSV files)
- 10X Genomics HDF5 (.h5)
- H5AD (AnnData format)
- CSV/Excel files
"""

from .loaders import (
    load_10x_mtx,
    load_10x_h5,
    load_h5ad,
    load_csv,
    auto_detect_format,
    get_data_info,
    DataLoader
)

from .validators import (
    validate_10x_data,
    validate_cell_barcodes,
    validate_gene_features,
    DataValidator
)

from .formats import (
    DataFormat,
    get_supported_formats,
    detect_file_format
)

__all__ = [
    # Loaders
    'load_10x_mtx',
    'load_10x_h5', 
    'load_h5ad',
    'load_csv',
    'auto_detect_format',
    'get_data_info',
    'DataLoader',
    
    # Validators
    'validate_10x_data',
    'validate_cell_barcodes',
    'validate_gene_features', 
    'DataValidator',
    
    # Formats
    'DataFormat',
    'get_supported_formats',
    'detect_file_format'
] 