"""
Data Validators for SingleCellStudio

This module provides validation functions to check data quality
and integrity for single cell RNA-seq datasets.
"""

import numpy as np
import pandas as pd
import anndata as ad
from scipy import sparse
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Exception raised when data validation fails"""
    pass

class ValidationWarning(UserWarning):
    """Warning raised for data quality issues"""
    pass

class DataValidator:
    """Main data validator class"""
    
    def __init__(self):
        self.validation_results = {}
    
    def validate_adata(self, adata: ad.AnnData, 
                      strict: bool = False) -> Dict[str, Any]:
        """
        Comprehensive validation of AnnData object
        
        Args:
            adata: AnnData object to validate
            strict: If True, raise exceptions for warnings
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': {},
            'recommendations': []
        }
        
        # Basic structure validation
        try:
            self._validate_basic_structure(adata, results)
            self._validate_dimensions(adata, results)
            self._validate_data_types(adata, results)
            self._validate_gene_names(adata, results)
            self._validate_cell_barcodes(adata, results)
            self._validate_data_quality(adata, results)
            
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Validation failed: {str(e)}")
        
        # Summary
        results['info']['n_errors'] = len(results['errors'])
        results['info']['n_warnings'] = len(results['warnings'])
        
        if results['errors']:
            results['valid'] = False
        
        if strict and results['warnings']:
            results['valid'] = False
        
        self.validation_results = results
        return results
    
    def _validate_basic_structure(self, adata: ad.AnnData, results: Dict):
        """Validate basic AnnData structure"""
        
        # Check if X matrix exists
        if adata.X is None:
            results['errors'].append("No expression matrix (X) found")
            return
        
        # Check if obs and var exist
        if adata.obs is None:
            results['errors'].append("No observation metadata (obs) found")
        
        if adata.var is None:
            results['errors'].append("No variable metadata (var) found")
        
        # Check dimensions match
        if adata.X.shape[0] != adata.n_obs:
            results['errors'].append(f"Matrix rows ({adata.X.shape[0]}) don't match obs ({adata.n_obs})")
        
        if adata.X.shape[1] != adata.n_vars:
            results['errors'].append(f"Matrix columns ({adata.X.shape[1]}) don't match var ({adata.n_vars})")
    
    def _validate_dimensions(self, adata: ad.AnnData, results: Dict):
        """Validate data dimensions"""
        
        n_cells = adata.n_obs
        n_genes = adata.n_vars
        
        results['info']['n_cells'] = n_cells
        results['info']['n_genes'] = n_genes
        
        # Check for reasonable dimensions
        if n_cells == 0:
            results['errors'].append("No cells found in dataset")
        elif n_cells < 10:
            results['warnings'].append(f"Very few cells ({n_cells}), results may be unreliable")
        elif n_cells > 1000000:
            results['warnings'].append(f"Very large dataset ({n_cells} cells), processing may be slow")
        
        if n_genes == 0:
            results['errors'].append("No genes found in dataset")
        elif n_genes < 100:
            results['warnings'].append(f"Very few genes ({n_genes}), dataset may be incomplete")
        elif n_genes > 100000:
            results['warnings'].append(f"Very large gene set ({n_genes}), consider filtering")
    
    def _validate_data_types(self, adata: ad.AnnData, results: Dict):
        """Validate data types and formats"""
        
        # Check X matrix type
        if hasattr(adata.X, 'dtype'):
            dtype = adata.X.dtype
            results['info']['matrix_dtype'] = str(dtype)
            
            if dtype == np.bool_:
                results['warnings'].append("Expression matrix is boolean, consider using counts")
            elif not np.issubdtype(dtype, np.number):
                results['errors'].append(f"Expression matrix has non-numeric dtype: {dtype}")
        
        # Check for sparse vs dense
        if sparse.issparse(adata.X):
            results['info']['matrix_format'] = 'sparse'
            results['info']['sparsity'] = 1.0 - (adata.X.nnz / np.prod(adata.X.shape))
        else:
            results['info']['matrix_format'] = 'dense'
            # Calculate sparsity for dense matrices
            zeros = np.sum(adata.X == 0)
            results['info']['sparsity'] = zeros / np.prod(adata.X.shape)
        
        # Recommend sparse format for highly sparse data
        if results['info']['sparsity'] > 0.9 and results['info']['matrix_format'] == 'dense':
            results['recommendations'].append("Consider converting to sparse format to save memory")
    
    def _validate_gene_names(self, adata: ad.AnnData, results: Dict):
        """Validate gene names and identifiers"""
        
        gene_names = adata.var_names
        
        # Check for duplicates
        duplicates = gene_names.duplicated()
        if duplicates.any():
            n_dups = duplicates.sum()
            results['warnings'].append(f"Found {n_dups} duplicate gene names")
            results['recommendations'].append("Consider making gene names unique")
        
        # Check for empty/null names
        empty_names = gene_names.isnull() | (gene_names == '')
        if empty_names.any():
            n_empty = empty_names.sum()
            results['warnings'].append(f"Found {n_empty} empty/null gene names")
        
        # Check gene name format
        results['info']['gene_name_examples'] = gene_names[:5].tolist()
        
        # Check for common gene ID formats
        if gene_names.str.startswith('ENSG').any():
            results['info']['gene_id_format'] = 'Ensembl'
        elif gene_names.str.match(r'^[A-Z]+[0-9]*$').any():
            results['info']['gene_id_format'] = 'Gene Symbol'
        else:
            results['info']['gene_id_format'] = 'Unknown'
    
    def _validate_cell_barcodes(self, adata: ad.AnnData, results: Dict):
        """Validate cell barcodes and identifiers"""
        
        cell_names = adata.obs_names
        
        # Check for duplicates
        duplicates = cell_names.duplicated()
        if duplicates.any():
            n_dups = duplicates.sum()
            results['errors'].append(f"Found {n_dups} duplicate cell barcodes")
        
        # Check for empty/null names
        empty_names = cell_names.isnull() | (cell_names == '')
        if empty_names.any():
            n_empty = empty_names.sum()
            results['warnings'].append(f"Found {n_empty} empty/null cell barcodes")
        
        # Check barcode format
        results['info']['cell_barcode_examples'] = cell_names[:5].tolist()
        
        # Check for 10X barcode format
        if cell_names.str.match(r'^[ATCG]+-[0-9]+$').any():
            results['info']['barcode_format'] = '10X Genomics'
        else:
            results['info']['barcode_format'] = 'Custom'
    
    def _validate_data_quality(self, adata: ad.AnnData, results: Dict):
        """Validate data quality metrics"""
        
        # Basic statistics
        if hasattr(adata.X, 'data'):  # Sparse matrix
            data = adata.X.data
        else:  # Dense matrix
            data = adata.X.flatten()
        
        # Remove zeros for statistics
        nonzero_data = data[data > 0] if len(data) > 0 else np.array([])
        
        if len(nonzero_data) > 0:
            results['info']['mean_expression'] = float(np.mean(nonzero_data))
            results['info']['median_expression'] = float(np.median(nonzero_data))
            results['info']['max_expression'] = float(np.max(nonzero_data))
            results['info']['min_nonzero_expression'] = float(np.min(nonzero_data))
        else:
            results['errors'].append("All expression values are zero")
            return
        
        # Check for negative values
        if np.any(data < 0):
            results['warnings'].append("Found negative expression values")
        
        # Check for very large values (possible normalization issues)
        if results['info']['max_expression'] > 1000:
            results['warnings'].append("Found very large expression values, check if data is normalized")
        
        # Per-cell statistics
        if sparse.issparse(adata.X):
            genes_per_cell = np.array(adata.X.sum(axis=1)).flatten()
            cells_per_gene = np.array(adata.X.sum(axis=0)).flatten()
        else:
            genes_per_cell = adata.X.sum(axis=1)
            cells_per_gene = adata.X.sum(axis=0)
        
        # Genes per cell
        results['info']['mean_genes_per_cell'] = float(np.mean(genes_per_cell))
        results['info']['median_genes_per_cell'] = float(np.median(genes_per_cell))
        
        # Cells per gene
        results['info']['mean_cells_per_gene'] = float(np.mean(cells_per_gene))
        results['info']['median_cells_per_gene'] = float(np.median(cells_per_gene))
        
        # Check for empty cells/genes
        empty_cells = np.sum(genes_per_cell == 0)
        empty_genes = np.sum(cells_per_gene == 0)
        
        if empty_cells > 0:
            results['warnings'].append(f"Found {empty_cells} empty cells (no gene expression)")
            results['recommendations'].append("Consider filtering empty cells")
        
        if empty_genes > 0:
            results['warnings'].append(f"Found {empty_genes} empty genes (not expressed in any cell)")
            results['recommendations'].append("Consider filtering unexpressed genes")
        
        # Check for low-quality cells
        low_gene_cells = np.sum(genes_per_cell < 200)
        if low_gene_cells > 0:
            pct = (low_gene_cells / len(genes_per_cell)) * 100
            results['warnings'].append(f"Found {low_gene_cells} ({pct:.1f}%) cells with <200 genes")
            results['recommendations'].append("Consider quality filtering based on gene count")

def validate_10x_data(folder_path: str) -> Dict[str, Any]:
    """
    Validate 10X Genomics data format
    
    Args:
        folder_path: Path to 10X data folder
        
    Returns:
        Validation results
    """
    from pathlib import Path
    
    folder_path = Path(folder_path)
    results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'info': {}
    }
    
    # Check if folder exists
    if not folder_path.exists():
        results['valid'] = False
        results['errors'].append(f"Folder does not exist: {folder_path}")
        return results
    
    # Check for required files
    required_files = ['matrix.mtx.gz', 'barcodes.tsv.gz', 'features.tsv.gz']
    alternative_files = ['matrix.mtx', 'barcodes.tsv', 'features.tsv']
    legacy_files = ['matrix.mtx.gz', 'barcodes.tsv.gz', 'genes.tsv.gz']
    
    # Check main format
    has_required = all((folder_path / f).exists() for f in required_files)
    has_alternative = all((folder_path / f).exists() for f in alternative_files)
    has_legacy = all((folder_path / f).exists() for f in legacy_files)
    
    if not (has_required or has_alternative or has_legacy):
        results['valid'] = False
        results['errors'].append("Missing required 10X files")
        results['info']['missing_files'] = [
            f for f in required_files 
            if not (folder_path / f).exists()
        ]
        return results
    
    # Determine format
    if has_required:
        results['info']['format'] = '10X v3 (compressed)'
        file_set = required_files
    elif has_legacy:
        results['info']['format'] = '10X v2 (legacy, compressed)'
        file_set = legacy_files
    else:
        results['info']['format'] = '10X (uncompressed)'
        file_set = alternative_files
    
    # Check file sizes
    for filename in file_set:
        filepath = folder_path / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            results['info'][f'{filename}_size_mb'] = round(size_mb, 2)
            
            if size_mb == 0:
                results['warnings'].append(f"Empty file: {filename}")
    
    return results

def validate_cell_barcodes(barcodes: pd.Index) -> Dict[str, Any]:
    """
    Validate cell barcode format and quality
    
    Args:
        barcodes: Cell barcode index
        
    Returns:
        Validation results
    """
    results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'info': {}
    }
    
    results['info']['n_barcodes'] = len(barcodes)
    
    # Check for duplicates
    if barcodes.duplicated().any():
        n_dups = barcodes.duplicated().sum()
        results['errors'].append(f"Found {n_dups} duplicate barcodes")
        results['valid'] = False
    
    # Check for empty barcodes
    empty = barcodes.isnull() | (barcodes == '')
    if empty.any():
        n_empty = empty.sum()
        results['warnings'].append(f"Found {n_empty} empty barcodes")
    
    # Check barcode format
    if len(barcodes) > 0:
        sample_barcode = str(barcodes[0])
        results['info']['sample_barcode'] = sample_barcode
        results['info']['barcode_length'] = len(sample_barcode)
        
        # Check for 10X format
        if '-' in sample_barcode:
            parts = sample_barcode.split('-')
            if len(parts) == 2 and parts[0].replace('N', 'A').isalpha():
                results['info']['format'] = '10X Genomics'
            else:
                results['info']['format'] = 'Custom with separator'
        else:
            results['info']['format'] = 'Custom'
    
    return results

def validate_gene_features(features: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate gene feature information
    
    Args:
        features: Gene feature DataFrame
        
    Returns:
        Validation results
    """
    results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'info': {}
    }
    
    results['info']['n_features'] = len(features)
    
    if len(features) == 0:
        results['errors'].append("No gene features found")
        results['valid'] = False
        return results
    
    # Check for required columns
    if 'gene_ids' in features.columns:
        gene_ids = features['gene_ids']
        
        # Check for duplicates
        if gene_ids.duplicated().any():
            n_dups = gene_ids.duplicated().sum()
            results['warnings'].append(f"Found {n_dups} duplicate gene IDs")
        
        # Check for empty IDs
        empty = gene_ids.isnull() | (gene_ids == '')
        if empty.any():
            n_empty = empty.sum()
            results['warnings'].append(f"Found {n_empty} empty gene IDs")
    
    if 'gene_symbols' in features.columns:
        gene_symbols = features['gene_symbols']
        
        # Check for duplicates
        if gene_symbols.duplicated().any():
            n_dups = gene_symbols.duplicated().sum()
            results['warnings'].append(f"Found {n_dups} duplicate gene symbols")
        
        # Sample gene symbols
        results['info']['sample_gene_symbols'] = gene_symbols.head(5).tolist()
    
    # Check feature types
    if 'feature_types' in features.columns:
        feature_types = features['feature_types'].value_counts()
        results['info']['feature_types'] = feature_types.to_dict()
        
        if 'Gene Expression' not in feature_types:
            results['warnings'].append("No 'Gene Expression' features found")
    
    return results 