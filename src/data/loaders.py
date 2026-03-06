"""
Data Loaders for SingleCellStudio

This module provides functions to load various single cell RNA-seq data formats
into AnnData objects for analysis.
"""

import os
import gzip
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple
import logging

import pandas as pd
import numpy as np
import anndata as ad
import scanpy as sc
from scipy import sparse
from scipy.io import mmread

from .formats import DataFormat, detect_file_format, validate_format_requirements

logger = logging.getLogger(__name__)

class DataLoadError(Exception):
    """Exception raised when data loading fails"""
    pass

class DataLoader:
    """Main data loader class with support for multiple formats"""
    
    def __init__(self):
        self.supported_formats = {
            DataFormat.TENX_MTX: self.load_10x_mtx,
            DataFormat.TENX_H5: self.load_10x_h5,
            DataFormat.H5AD: self.load_h5ad,
            DataFormat.CSV: self.load_csv,
            DataFormat.TSV: self.load_csv,  # TSV is handled by CSV loader
            DataFormat.CSV_GZ: self.load_csv,
            DataFormat.TSV_GZ: self.load_csv,
        }
    
    def load(self, 
             file_path: Union[str, Path], 
             format_type: Optional[DataFormat] = None,
             **kwargs) -> ad.AnnData:
        """
        Load data from file/folder into AnnData object
        
        Args:
            file_path: Path to data file or folder
            format_type: Data format (auto-detected if None)
            **kwargs: Additional arguments passed to specific loaders
            
        Returns:
            AnnData object containing the loaded data
            
        Raises:
            DataLoadError: If loading fails
        """
        file_path = Path(file_path)
        
        # Auto-detect format if not specified
        if format_type is None:
            format_type = detect_file_format(file_path)
            logger.info(f"Auto-detected format: {format_type.value}")
        
        # Validate format requirements
        if not validate_format_requirements(file_path, format_type):
            raise DataLoadError(f"File/folder does not meet requirements for {format_type.value}")
        
        # Check if format is supported
        if format_type not in self.supported_formats:
            raise DataLoadError(f"Unsupported format: {format_type.value}")
        
        # Load data using appropriate loader
        try:
            loader_func = self.supported_formats[format_type]
            adata = loader_func(file_path, **kwargs)
            
            # Add metadata about the loaded data
            adata.uns['scs_metadata'] = {
                'source_path': str(file_path),
                'format': format_type.value,
                'loaded_at': pd.Timestamp.now().isoformat()
            }
            
            logger.info(f"Successfully loaded data: {adata.n_obs} cells × {adata.n_vars} genes")
            return adata
            
        except Exception as e:
            raise DataLoadError(f"Failed to load {format_type.value} data from {file_path}: {str(e)}")
    
    def load_10x_mtx(self, folder_path: Path, **kwargs) -> ad.AnnData:
        """Load 10X Genomics MTX format data"""
        return load_10x_mtx(folder_path, **kwargs)
    
    def load_10x_h5(self, file_path: Path, **kwargs) -> ad.AnnData:
        """Load 10X Genomics HDF5 format data"""
        return load_10x_h5(file_path, **kwargs)
    
    def load_h5ad(self, file_path: Path, **kwargs) -> ad.AnnData:
        """Load H5AD format data"""
        return load_h5ad(file_path, **kwargs)
    
    def load_csv(self, file_path: Path, **kwargs) -> ad.AnnData:
        """Load CSV/TSV format data"""
        return load_csv(file_path, **kwargs)

def load_10x_mtx(folder_path: Union[str, Path], 
                 var_names: str = 'gene_symbols',
                 cache: bool = False,
                 **kwargs) -> ad.AnnData:
    """
    Load 10X Genomics MTX format data
    
    Args:
        folder_path: Path to folder containing matrix.mtx.gz, barcodes.tsv.gz, features.tsv.gz
        var_names: Use 'gene_symbols' or 'gene_ids' for gene names
        cache: Whether to cache the loaded data
        **kwargs: Additional arguments
        
    Returns:
        AnnData object
    """
    folder_path = Path(folder_path)
    logger.info(f"Loading 10X MTX data from: {folder_path}")
    
    try:
        # Use scanpy's built-in 10X loader
        adata = sc.read_10x_mtx(
            folder_path,
            var_names=var_names,
            cache=cache,
            **kwargs
        )
        
        # Make variable names unique (in case of duplicates)
        try:
            adata.var_names_unique()
        except AttributeError:
            # Fallback for older AnnData versions
            adata.var_names = pd.Index(adata.var_names).unique()
        
        # Make observation names unique
        try:
            adata.obs_names_unique()
        except AttributeError:
            # Fallback for older AnnData versions  
            adata.obs_names = pd.Index(adata.obs_names).unique()
        
        logger.info(f"Loaded 10X MTX data: {adata.n_obs} cells × {adata.n_vars} genes")
        return adata
        
    except Exception as e:
        # Try manual loading if scanpy fails
        logger.warning(f"Scanpy loading failed, trying manual loading: {e}")
        return _load_10x_mtx_manual(folder_path, var_names)

def _load_10x_mtx_manual(folder_path: Path, var_names: str = 'gene_symbols') -> ad.AnnData:
    """Manually load 10X MTX data when scanpy fails"""
    
    # Find the required files (with different possible names)
    matrix_file = None
    barcodes_file = None
    features_file = None
    
    # Look for matrix file
    for name in ['matrix.mtx.gz', 'matrix.mtx']:
        if (folder_path / name).exists():
            matrix_file = folder_path / name
            break
    
    # Look for barcodes file
    for name in ['barcodes.tsv.gz', 'barcodes.tsv']:
        if (folder_path / name).exists():
            barcodes_file = folder_path / name
            break
    
    # Look for features file (new format) or genes file (old format)
    for name in ['features.tsv.gz', 'features.tsv', 'genes.tsv.gz', 'genes.tsv']:
        if (folder_path / name).exists():
            features_file = folder_path / name
            break
    
    if not all([matrix_file, barcodes_file, features_file]):
        raise DataLoadError(f"Missing required files in {folder_path}")
    
    logger.info(f"Loading files: {matrix_file.name}, {barcodes_file.name}, {features_file.name}")
    
    # Load matrix
    if matrix_file.suffix == '.gz':
        with gzip.open(matrix_file, 'rt') as f:
            matrix = mmread(f).T.tocsr()  # Transpose to get cells × genes
    else:
        matrix = mmread(matrix_file).T.tocsr()
    
    # Load barcodes
    if barcodes_file.suffix == '.gz':
        barcodes = pd.read_csv(barcodes_file, header=None, sep='\t', compression='gzip')[0].values
    else:
        barcodes = pd.read_csv(barcodes_file, header=None, sep='\t')[0].values
    
    # Load features/genes
    if features_file.suffix == '.gz':
        features = pd.read_csv(features_file, header=None, sep='\t', compression='gzip')
    else:
        features = pd.read_csv(features_file, header=None, sep='\t')
    
    # Handle different feature file formats
    if features.shape[1] >= 2:
        gene_ids = features[0].values
        gene_symbols = features[1].values
        
        # Use third column as feature type if available
        if features.shape[1] >= 3:
            feature_types = features[2].values
        else:
            feature_types = ['Gene Expression'] * len(gene_ids)
    else:
        # Old format with only gene IDs
        gene_ids = features[0].values
        gene_symbols = gene_ids.copy()
        feature_types = ['Gene Expression'] * len(gene_ids)
    
    # Create AnnData object
    adata = ad.AnnData(
        X=matrix,
        obs=pd.DataFrame(index=barcodes),
        var=pd.DataFrame({
            'gene_ids': gene_ids,
            'gene_symbols': gene_symbols,
            'feature_types': feature_types
        }, index=gene_ids if var_names == 'gene_ids' else gene_symbols)
    )
    
    # Make names unique
    try:
        adata.var_names_unique()
    except AttributeError:
        # Fallback for older AnnData versions
        adata.var_names = pd.Index(adata.var_names).unique()
    
    try:
        adata.obs_names_unique()
    except AttributeError:
        # Fallback for older AnnData versions  
        adata.obs_names = pd.Index(adata.obs_names).unique()
    
    logger.info(f"Manually loaded 10X MTX data: {adata.n_obs} cells × {adata.n_vars} genes")
    return adata

def load_10x_h5(file_path: Union[str, Path], 
                genome: Optional[str] = None,
                **kwargs) -> ad.AnnData:
    """
    Load 10X Genomics HDF5 format data
    
    Args:
        file_path: Path to .h5 file
        genome: Genome to load (if multiple genomes in file)
        **kwargs: Additional arguments
        
    Returns:
        AnnData object
    """
    file_path = Path(file_path)
    logger.info(f"Loading 10X H5 data from: {file_path}")
    
    try:
        # Use scanpy's built-in 10X H5 loader
        adata = sc.read_10x_h5(file_path, genome=genome, **kwargs)
        
        # Make variable names unique
        try:
            adata.var_names_make_unique()
        except Exception as e:
            logger.warning(f"Could not make var_names unique: {e}")
            # Try manual approach for duplicate gene names
            try:
                # Count duplicates and add suffix
                var_names = adata.var_names.tolist()
                seen = {}
                unique_names = []
                for name in var_names:
                    if name in seen:
                        seen[name] += 1
                        unique_names.append(f"{name}_{seen[name]}")
                    else:
                        seen[name] = 0
                        unique_names.append(name)
                adata.var_names = unique_names
                logger.info(f"Manually made {len(seen)} gene names unique")
            except Exception as e2:
                logger.warning(f"Could not manually fix var_names: {e2}")
        
        # Make observation names unique  
        try:
            adata.obs_names_make_unique()
        except Exception as e:
            logger.warning(f"Could not make obs_names unique: {e}")
        
        logger.info(f"Loaded 10X H5 data: {adata.n_obs} cells × {adata.n_vars} genes")
        return adata
        
    except Exception as e:
        raise DataLoadError(f"Failed to load 10X H5 data: {e}")

def load_h5ad(file_path: Union[str, Path], **kwargs) -> ad.AnnData:
    """
    Load H5AD format data
    
    Args:
        file_path: Path to .h5ad file
        **kwargs: Additional arguments for anndata.read_h5ad
        
    Returns:
        AnnData object
    """
    file_path = Path(file_path)
    logger.info(f"Loading H5AD data from: {file_path}")
    
    try:
        adata = ad.read_h5ad(file_path, **kwargs)
        logger.info(f"Loaded H5AD data: {adata.n_obs} cells × {adata.n_vars} genes")
        return adata
        
    except Exception as e:
        raise DataLoadError(f"Failed to load H5AD data: {e}")

def load_csv(file_path: Union[str, Path], 
             first_column_names: bool = True,
             delimiter: Optional[str] = None,
             **kwargs) -> ad.AnnData:
    """
    Load CSV/TSV format data
    
    Args:
        file_path: Path to CSV/TSV file
        first_column_names: Whether first column contains row names
        delimiter: Column delimiter (auto-detected if None)
        **kwargs: Additional arguments for pandas.read_csv
        
    Returns:
        AnnData object
    """
    file_path = Path(file_path)
    logger.info(f"Loading CSV/TSV data from: {file_path}")
    
    # Auto-detect delimiter
    if delimiter is None:
        if file_path.suffix.lower() in ['.tsv', '.txt'] or 'tsv' in file_path.name.lower():
            delimiter = '\t'
        else:
            delimiter = ','
    
    # Handle compression
    compression = None
    if file_path.suffix == '.gz':
        compression = 'gzip'
    
    try:
        # Read the data
        if first_column_names:
            df = pd.read_csv(file_path, sep=delimiter, index_col=0, compression=compression, **kwargs)
        else:
            df = pd.read_csv(file_path, sep=delimiter, compression=compression, **kwargs)
        
        # Convert to AnnData (assuming genes are columns, cells are rows)
        adata = ad.AnnData(df)
        
        logger.info(f"Loaded CSV/TSV data: {adata.n_obs} cells × {adata.n_vars} genes")
        return adata
        
    except Exception as e:
        raise DataLoadError(f"Failed to load CSV/TSV data: {e}")

def auto_detect_format(file_path: Union[str, Path]) -> DataFormat:
    """
    Auto-detect the format of a data file or folder
    
    Args:
        file_path: Path to file or folder
        
    Returns:
        Detected DataFormat
    """
    return detect_file_format(Path(file_path))

def get_data_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get information about a data file without fully loading it
    
    Args:
        file_path: Path to file or folder
        
    Returns:
        Dictionary with data information
    """
    file_path = Path(file_path)
    format_type = detect_file_format(file_path)
    
    info = {
        'path': str(file_path),
        'format': format_type.value,
        'exists': file_path.exists(),
        'size_mb': None,
        'n_cells': None,
        'n_genes': None,
        'error': None
    }
    
    if not file_path.exists():
        info['error'] = 'File/folder does not exist'
        return info
    
    try:
        # Get file size
        if file_path.is_file():
            info['size_mb'] = file_path.stat().st_size / (1024 * 1024)
        elif file_path.is_dir():
            total_size = sum(f.stat().st_size for f in file_path.rglob('*') if f.is_file())
            info['size_mb'] = total_size / (1024 * 1024)
        
        # Try to get dimensions without fully loading
        if format_type == DataFormat.TENX_MTX:
            info.update(_get_10x_mtx_info(file_path))
        elif format_type == DataFormat.TENX_H5:
            info.update(_get_10x_h5_info(file_path))
        elif format_type == DataFormat.H5AD:
            info.update(_get_h5ad_info(file_path))
        
    except Exception as e:
        info['error'] = str(e)
    
    return info

def _get_10x_mtx_info(folder_path: Path) -> Dict[str, Any]:
    """Get info about 10X MTX data without fully loading"""
    info = {}
    
    # Find barcodes file to count cells
    for name in ['barcodes.tsv.gz', 'barcodes.tsv']:
        barcodes_file = folder_path / name
        if barcodes_file.exists():
            if name.endswith('.gz'):
                with gzip.open(barcodes_file, 'rt') as f:
                    info['n_cells'] = sum(1 for _ in f)
            else:
                with open(barcodes_file, 'r') as f:
                    info['n_cells'] = sum(1 for _ in f)
            break
    
    # Find features file to count genes
    for name in ['features.tsv.gz', 'features.tsv', 'genes.tsv.gz', 'genes.tsv']:
        features_file = folder_path / name
        if features_file.exists():
            if name.endswith('.gz'):
                with gzip.open(features_file, 'rt') as f:
                    info['n_genes'] = sum(1 for _ in f)
            else:
                with open(features_file, 'r') as f:
                    info['n_genes'] = sum(1 for _ in f)
            break
    
    return info

def _get_10x_h5_info(file_path: Path) -> Dict[str, Any]:
    """Get info about 10X H5 data without fully loading"""
    import h5py
    
    info = {}
    try:
        with h5py.File(file_path, 'r') as f:
            # Look for matrix group (common structure)
            if 'matrix' in f:
                matrix_group = f['matrix']
                if 'shape' in matrix_group:
                    shape = matrix_group['shape'][:]
                    info['n_genes'] = int(shape[0])
                    info['n_cells'] = int(shape[1])
                elif 'barcodes' in matrix_group and 'features' in matrix_group:
                    info['n_cells'] = len(matrix_group['barcodes'])
                    info['n_genes'] = len(matrix_group['features'])
    except Exception:
        pass  # Info will remain empty
    
    return info

def _get_h5ad_info(file_path: Path) -> Dict[str, Any]:
    """Get info about H5AD data without fully loading"""
    import h5py
    
    info = {}
    try:
        with h5py.File(file_path, 'r') as f:
            if 'obs' in f and 'var' in f:
                info['n_cells'] = f['obs'].shape[0]
                info['n_genes'] = f['var'].shape[0]
    except Exception:
        pass  # Info will remain empty
    
    return info 