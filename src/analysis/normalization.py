"""
Normalization Module for Single Cell Analysis

This module provides various normalization methods for single cell RNA-seq data
including log normalization, CPM, TPM, and advanced methods like SCTransform.
"""

import numpy as np
import pandas as pd
import scanpy as sc
from typing import Dict, List, Optional, Tuple, Union, Literal
import logging
from scipy import sparse
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Normalizer:
    """
    Comprehensive normalization for single cell data
    
    This class provides various normalization methods commonly used
    in single cell RNA-seq analysis.
    """
    
    def __init__(self, adata=None):
        """
        Initialize Normalizer
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        """
        self.adata = adata
        self.normalization_history = []
        
    def log_normalize(self, adata=None, target_sum=1e4, exclude_highly_expressed=False,
                     max_fraction=0.05, key_added=None, copy=False):
        """
        Normalize counts per cell and log transform (log1p)
        
        This is the most common normalization method in single cell analysis.
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        target_sum : float
            Target sum for normalization (default: 10,000)
        exclude_highly_expressed : bool
            Exclude highly expressed genes from normalization
        max_fraction : float
            Maximum fraction for highly expressed genes
        key_added : str, optional
            Key to add normalized data to layers
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Normalized data if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if adata is None:
            raise ValueError("No data provided for normalization")
            
        if copy:
            adata = adata.copy()
            
        logger.info(f"Performing log normalization with target sum {target_sum}")
        
        # Store raw data if not already stored
        if adata.raw is None:
            adata.raw = adata
            
        # Normalize to target sum
        sc.pp.normalize_total(adata, target_sum=target_sum, 
                            exclude_highly_expressed=exclude_highly_expressed,
                            max_fraction=max_fraction, key_added=key_added)
        
        # Log transform
        sc.pp.log1p(adata)
        
        # Record normalization
        self.normalization_history.append({
            'method': 'log_normalize',
            'target_sum': target_sum,
            'exclude_highly_expressed': exclude_highly_expressed,
            'max_fraction': max_fraction
        })
        
        logger.info("Log normalization completed")
        
        if copy:
            return adata
            
    def cpm_normalize(self, adata=None, copy=False):
        """
        Counts Per Million (CPM) normalization
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Normalized data if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if copy:
            adata = adata.copy()
            
        logger.info("Performing CPM normalization")
        
        # Store raw data if not already stored
        if adata.raw is None:
            adata.raw = adata
            
        # CPM normalization
        sc.pp.normalize_total(adata, target_sum=1e6)
        
        # Record normalization
        self.normalization_history.append({
            'method': 'cpm_normalize',
            'target_sum': 1e6
        })
        
        logger.info("CPM normalization completed")
        
        if copy:
            return adata
            
    def tpm_normalize(self, adata=None, gene_lengths=None, copy=False):
        """
        Transcripts Per Million (TPM) normalization
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        gene_lengths : dict or pd.Series, optional
            Gene lengths for TPM calculation
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Normalized data if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if copy:
            adata = adata.copy()
            
        logger.info("Performing TPM normalization")
        
        if gene_lengths is None:
            logger.warning("No gene lengths provided, using uniform length (TPM = CPM)")
            # Fall back to CPM if no gene lengths
            return self.cpm_normalize(adata, copy=False)
            
        # Store raw data if not already stored
        if adata.raw is None:
            adata.raw = adata
            
        # Get gene lengths for genes in dataset
        if isinstance(gene_lengths, dict):
            lengths = pd.Series(gene_lengths)
        else:
            lengths = gene_lengths
            
        # Filter to genes present in data
        common_genes = adata.var_names.intersection(lengths.index)
        if len(common_genes) == 0:
            raise ValueError("No common genes found between data and gene lengths")
            
        logger.info(f"Using gene lengths for {len(common_genes)} genes")
        
        # Subset data and lengths
        adata_subset = adata[:, common_genes]
        lengths_subset = lengths[common_genes]
        
        # Calculate TPM
        # 1. Divide by gene length (in kb)
        length_kb = lengths_subset / 1000
        rpk = adata_subset.X / length_kb.values
        
        # 2. Normalize by total RPK per cell and multiply by 1e6
        total_rpk = np.array(rpk.sum(axis=1)).flatten()
        tpm = (rpk / total_rpk[:, np.newaxis]) * 1e6
        
        # Update data
        adata_subset.X = tpm
        
        # Record normalization
        self.normalization_history.append({
            'method': 'tpm_normalize',
            'genes_with_lengths': len(common_genes),
            'total_genes': adata.n_vars
        })
        
        logger.info("TPM normalization completed")
        
        if copy:
            return adata_subset
        else:
            # Update original data (only for genes with lengths)
            adata._inplace_subset_var(common_genes)
            adata.X = tpm
            
    def quantile_normalize(self, adata=None, copy=False):
        """
        Quantile normalization
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Normalized data if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if copy:
            adata = adata.copy()
            
        logger.info("Performing quantile normalization")
        
        # Store raw data if not already stored
        if adata.raw is None:
            adata.raw = adata
            
        # Convert to dense if sparse
        if sparse.issparse(adata.X):
            X = adata.X.toarray()
        else:
            X = adata.X.copy()
            
        # Quantile normalization
        X_sorted = np.sort(X, axis=0)
        X_mean = np.mean(X_sorted, axis=1)
        
        # Get ranks
        X_ranks = np.empty_like(X)
        for i in range(X.shape[1]):
            X_ranks[:, i] = np.argsort(np.argsort(X[:, i]))
            
        # Apply quantile normalization
        for i in range(X.shape[1]):
            X[:, i] = X_mean[X_ranks[:, i].astype(int)]
            
        adata.X = X
        
        # Record normalization
        self.normalization_history.append({
            'method': 'quantile_normalize'
        })
        
        logger.info("Quantile normalization completed")
        
        if copy:
            return adata
            
    def size_factor_normalize(self, adata=None, method='median', copy=False):
        """
        Size factor normalization (similar to DESeq2)
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        method : str
            Method for size factor calculation ('median' or 'geometric_mean')
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Normalized data if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if copy:
            adata = adata.copy()
            
        logger.info(f"Performing size factor normalization using {method}")
        
        # Store raw data if not already stored
        if adata.raw is None:
            adata.raw = adata
            
        # Calculate size factors
        if method == 'median':
            # Median of ratios method (DESeq2-like)
            # Calculate geometric mean for each gene
            if sparse.issparse(adata.X):
                X = adata.X.toarray()
            else:
                X = adata.X
                
            # Add pseudocount to avoid log(0)
            X_pseudo = X + 1
            
            # Geometric mean per gene
            geo_means = np.exp(np.mean(np.log(X_pseudo), axis=0))
            
            # Ratios to geometric means
            ratios = X_pseudo / geo_means
            
            # Size factors as median of ratios per cell
            size_factors = np.median(ratios, axis=1)
            
        elif method == 'geometric_mean':
            # Simple geometric mean of counts per cell
            if sparse.issparse(adata.X):
                # For sparse matrices, calculate differently
                size_factors = np.array(adata.X.sum(axis=1)).flatten()
            else:
                size_factors = np.array(adata.X.sum(axis=1)).flatten()
                
        # Normalize by size factors
        adata.X = adata.X / size_factors[:, np.newaxis]
        
        # Store size factors
        adata.obs['size_factors'] = size_factors
        
        # Record normalization
        self.normalization_history.append({
            'method': 'size_factor_normalize',
            'size_factor_method': method
        })
        
        logger.info("Size factor normalization completed")
        
        if copy:
            return adata
            
    def batch_correct_combat(self, adata=None, batch_key='batch', copy=False):
        """
        Batch correction using ComBat
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        batch_key : str
            Key in adata.obs containing batch information
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Batch-corrected data if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if copy:
            adata = adata.copy()
            
        if batch_key not in adata.obs.columns:
            raise ValueError(f"Batch key '{batch_key}' not found in adata.obs")
            
        logger.info(f"Performing ComBat batch correction using '{batch_key}'")
        
        try:
            # Use scanpy's combat implementation
            sc.pp.combat(adata, key=batch_key)
            
            # Record normalization
            self.normalization_history.append({
                'method': 'batch_correct_combat',
                'batch_key': batch_key
            })
            
            logger.info("ComBat batch correction completed")
            
        except Exception as e:
            logger.error(f"ComBat batch correction failed: {e}")
            raise
            
        if copy:
            return adata
            
    def scale_data(self, adata=None, zero_center=True, max_value=None, copy=False):
        """
        Scale data to unit variance (z-score normalization)
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        zero_center : bool
            Whether to center the data at zero
        max_value : float, optional
            Maximum value after scaling (clips outliers)
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Scaled data if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if copy:
            adata = adata.copy()
            
        logger.info("Scaling data to unit variance")
        
        # Scale using scanpy
        sc.pp.scale(adata, zero_center=zero_center, max_value=max_value)
        
        # Record normalization
        self.normalization_history.append({
            'method': 'scale_data',
            'zero_center': zero_center,
            'max_value': max_value
        })
        
        logger.info("Data scaling completed")
        
        if copy:
            return adata
            
    def get_normalization_history(self):
        """Get history of normalization steps applied"""
        return self.normalization_history
        
    def reset_to_raw(self, adata=None):
        """Reset data to raw counts"""
        if adata is None:
            adata = self.adata
            
        if adata.raw is None:
            logger.warning("No raw data stored, cannot reset")
            return
            
        logger.info("Resetting to raw data")
        adata.X = adata.raw.X.copy()
        self.normalization_history = []


def normalize_data(adata, method='log', target_sum=1e4, copy=False, **kwargs):
    """
    Convenience function for data normalization
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    method : str
        Normalization method ('log', 'cpm', 'tpm', 'quantile', 'size_factor')
    target_sum : float
        Target sum for normalization (for log and CPM methods)
    copy : bool
        Return a copy instead of modifying in place
    **kwargs : dict
        Additional arguments for specific normalization methods
        
    Returns:
    --------
    anndata.AnnData or None : Normalized data if copy=True
    """
    normalizer = Normalizer(adata)
    
    if method == 'log':
        return normalizer.log_normalize(target_sum=target_sum, copy=copy, **kwargs)
    elif method == 'cpm':
        return normalizer.cpm_normalize(copy=copy, **kwargs)
    elif method == 'tpm':
        return normalizer.tpm_normalize(copy=copy, **kwargs)
    elif method == 'quantile':
        return normalizer.quantile_normalize(copy=copy, **kwargs)
    elif method == 'size_factor':
        return normalizer.size_factor_normalize(copy=copy, **kwargs)
    elif method == 'scale':
        return normalizer.scale_data(copy=copy, **kwargs)
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def recommend_normalization(adata, data_type='counts'):
    """
    Recommend normalization method based on data characteristics
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    data_type : str
        Type of data ('counts', 'tpm', 'fpkm', 'unknown')
        
    Returns:
    --------
    dict : Normalization recommendations
    """
    recommendations = {
        'primary_method': None,
        'secondary_methods': [],
        'reasoning': [],
        'parameters': {}
    }
    
    # Check data characteristics
    X = adata.X
    if sparse.issparse(X):
        X = X.toarray()
        
    # Check if data looks like raw counts
    has_integers = np.allclose(X, X.astype(int), rtol=1e-10)
    max_value = np.max(X)
    mean_value = np.mean(X)
    
    if data_type == 'counts' or (has_integers and max_value > 100):
        # Raw counts data
        recommendations['primary_method'] = 'log'
        recommendations['secondary_methods'] = ['cpm', 'size_factor']
        recommendations['reasoning'].append("Data appears to be raw counts")
        recommendations['parameters']['target_sum'] = 1e4
        
    elif data_type == 'tpm' or (not has_integers and max_value < 1000 and mean_value < 10):
        # Already normalized data
        recommendations['primary_method'] = 'scale'
        recommendations['secondary_methods'] = ['quantile']
        recommendations['reasoning'].append("Data appears to be already normalized (TPM/FPKM-like)")
        
    else:
        # Unknown data type
        recommendations['primary_method'] = 'log'
        recommendations['secondary_methods'] = ['scale', 'quantile']
        recommendations['reasoning'].append("Data type unclear, recommending log normalization")
        recommendations['parameters']['target_sum'] = 1e4
        
    # Check for batch effects
    if 'batch' in adata.obs.columns:
        recommendations['secondary_methods'].append('batch_correct_combat')
        recommendations['reasoning'].append("Batch information detected")
        
    return recommendations


def log_normalize(adata, target_sum=1e4, exclude_highly_expressed=False,
                 max_fraction=0.05, key_added=None, copy=False):
    """
    Convenience function for log normalization
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    target_sum : float
        Target sum for normalization
    exclude_highly_expressed : bool
        Exclude highly expressed genes from normalization
    max_fraction : float
        Maximum fraction of total counts for highly expressed genes
    key_added : str, optional
        Key to add to adata.obs for size factors
    copy : bool
        Return a copy instead of modifying in place
        
    Returns:
    --------
    anndata.AnnData or None : Normalized data if copy=True
    """
    normalizer = Normalizer(adata)
    return normalizer.log_normalize(target_sum=target_sum, 
                                   exclude_highly_expressed=exclude_highly_expressed,
                                   max_fraction=max_fraction, 
                                   key_added=key_added, 
                                   copy=copy)


def scale_data(adata, zero_center=True, max_value=None, copy=False):
    """
    Convenience function for data scaling
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    zero_center : bool
        Whether to center the data at zero
    max_value : float, optional
        Maximum value after scaling (clips outliers)
    copy : bool
        Return a copy instead of modifying in place
        
    Returns:
    --------
    anndata.AnnData or None : Scaled data if copy=True
    """
    normalizer = Normalizer(adata)
    return normalizer.scale_data(zero_center=zero_center, 
                                max_value=max_value, 
                                copy=copy) 