"""
Quality Control Module for Single Cell Analysis

This module provides comprehensive quality control metrics calculation
and filtering for single cell RNA-seq data.
"""

import numpy as np
import pandas as pd
import scanpy as sc
from typing import Dict, List, Optional, Tuple, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QualityControl:
    """
    Comprehensive quality control for single cell data
    
    This class provides methods for calculating QC metrics, identifying
    outliers, and filtering cells and genes based on quality thresholds.
    """
    
    def __init__(self, adata=None):
        """
        Initialize QualityControl
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        """
        self.adata = adata
        self.qc_metrics = {}
        self.filter_stats = {}
        
    def calculate_qc_metrics(self, adata=None, mitochondrial_prefix='MT-', 
                           ribosomal_prefix='RP', hemoglobin_prefix='HB'):
        """
        Calculate comprehensive quality control metrics
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object. If None, uses self.adata
        mitochondrial_prefix : str
            Prefix for mitochondrial genes (default: 'MT-')
        ribosomal_prefix : str  
            Prefix for ribosomal genes (default: 'RP')
        hemoglobin_prefix : str
            Prefix for hemoglobin genes (default: 'HB')
            
        Returns:
        --------
        dict : Quality control metrics
        """
        if adata is None:
            adata = self.adata
            
        if adata is None:
            raise ValueError("No data provided for QC calculation")
            
        logger.info("Calculating quality control metrics...")
        
        # Basic metrics
        adata.var['mt'] = adata.var_names.str.startswith(mitochondrial_prefix)
        adata.var['ribo'] = adata.var_names.str.startswith(ribosomal_prefix) 
        adata.var['hb'] = adata.var_names.str.startswith(hemoglobin_prefix)
        
        # Calculate QC metrics using scanpy
        sc.pp.calculate_qc_metrics(adata, percent_top=None, log1p=False, inplace=True)
        
        # Additional custom metrics
        self._calculate_additional_metrics(adata)
        
        # Store metrics
        self.qc_metrics = {
            'n_cells': adata.n_obs,
            'n_genes': adata.n_vars,
            'total_counts': adata.obs['total_counts'].sum(),
            'mean_counts_per_cell': adata.obs['total_counts'].mean(),
            'median_counts_per_cell': adata.obs['total_counts'].median(),
            'mean_genes_per_cell': adata.obs['n_genes_by_counts'].mean(),
            'median_genes_per_cell': adata.obs['n_genes_by_counts'].median(),
            'mean_cells_per_gene': adata.var['n_cells_by_counts'].mean(),
            'median_cells_per_gene': adata.var['n_cells_by_counts'].median(),
            'mt_gene_count': adata.var['mt'].sum(),
            'ribo_gene_count': adata.var['ribo'].sum(),
            'hb_gene_count': adata.var['hb'].sum(),
        }
        
        # Calculate percentiles for thresholding
        self._calculate_percentiles(adata)
        
        logger.info(f"QC metrics calculated for {self.qc_metrics['n_cells']} cells and {self.qc_metrics['n_genes']} genes")
        
        return self.qc_metrics
        
    def _calculate_additional_metrics(self, adata):
        """Calculate additional QC metrics"""
        
        # Doublet scores (simplified)
        adata.obs['doublet_score'] = (adata.obs['total_counts'] / adata.obs['total_counts'].median()) * \
                                   (adata.obs['n_genes_by_counts'] / adata.obs['n_genes_by_counts'].median())
        
        # Complexity (genes per UMI)
        adata.obs['complexity'] = adata.obs['n_genes_by_counts'] / adata.obs['total_counts']
        
        # Log10 total counts
        adata.obs['log10_total_counts'] = np.log10(adata.obs['total_counts'] + 1)
        
    def _calculate_percentiles(self, adata):
        """Calculate percentiles for filtering thresholds"""
        
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        
        for metric in ['total_counts', 'n_genes_by_counts', 'pct_counts_mt']:
            if metric in adata.obs.columns:
                self.qc_metrics[f'{metric}_percentiles'] = {
                    f'p{p}': np.percentile(adata.obs[metric], p) for p in percentiles
                }
                
    def identify_outliers(self, adata=None, method='mad', n_mads=3):
        """
        Identify outlier cells using MAD (Median Absolute Deviation) or IQR
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        method : str
            Method for outlier detection ('mad' or 'iqr')
        n_mads : float
            Number of MADs for outlier threshold
            
        Returns:
        --------
        dict : Outlier identification results
        """
        if adata is None:
            adata = self.adata
            
        logger.info(f"Identifying outliers using {method} method...")
        
        outliers = {}
        
        for metric in ['total_counts', 'n_genes_by_counts', 'pct_counts_mt']:
            if metric in adata.obs.columns:
                if method == 'mad':
                    outliers[metric] = self._identify_outliers_mad(adata.obs[metric], n_mads)
                elif method == 'iqr':
                    outliers[metric] = self._identify_outliers_iqr(adata.obs[metric])
                    
        # Combined outliers
        outlier_cells = set()
        for metric_outliers in outliers.values():
            outlier_cells.update(metric_outliers)
            
        outliers['combined'] = list(outlier_cells)
        outliers['n_outliers'] = len(outlier_cells)
        outliers['outlier_fraction'] = len(outlier_cells) / adata.n_obs
        
        logger.info(f"Identified {len(outlier_cells)} outlier cells ({outliers['outlier_fraction']:.2%})")
        
        return outliers
        
    def _identify_outliers_mad(self, values, n_mads=3):
        """Identify outliers using MAD method"""
        median = np.median(values)
        mad = np.median(np.abs(values - median))
        threshold_low = median - n_mads * mad
        threshold_high = median + n_mads * mad
        
        outliers = np.where((values < threshold_low) | (values > threshold_high))[0]
        return outliers.tolist()
        
    def _identify_outliers_iqr(self, values, factor=1.5):
        """Identify outliers using IQR method"""
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        threshold_low = q1 - factor * iqr
        threshold_high = q3 + factor * iqr
        
        outliers = np.where((values < threshold_low) | (values > threshold_high))[0]
        return outliers.tolist()
        
    def filter_cells(self, adata=None, min_genes=200, max_genes=None, 
                    min_counts=None, max_counts=None, max_pct_mt=20,
                    max_pct_ribo=None, max_doublet_score=None):
        """
        Filter cells based on quality control metrics
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        min_genes : int
            Minimum number of genes per cell
        max_genes : int, optional
            Maximum number of genes per cell
        min_counts : int, optional
            Minimum total counts per cell
        max_counts : int, optional
            Maximum total counts per cell
        max_pct_mt : float
            Maximum percentage of mitochondrial genes
        max_pct_ribo : float, optional
            Maximum percentage of ribosomal genes
        max_doublet_score : float, optional
            Maximum doublet score
            
        Returns:
        --------
        anndata.AnnData : Filtered data
        """
        if adata is None:
            adata = self.adata.copy()
        else:
            adata = adata.copy()
            
        logger.info("Filtering cells based on QC metrics...")
        
        # Store original counts
        n_cells_orig = adata.n_obs
        
        # Apply filters
        filters = []
        
        if min_genes is not None:
            filter_min_genes = adata.obs['n_genes_by_counts'] >= min_genes
            filters.append(filter_min_genes)
            logger.info(f"Min genes filter: {filter_min_genes.sum()} cells pass")
            
        if max_genes is not None:
            filter_max_genes = adata.obs['n_genes_by_counts'] <= max_genes
            filters.append(filter_max_genes)
            logger.info(f"Max genes filter: {filter_max_genes.sum()} cells pass")
            
        if min_counts is not None:
            filter_min_counts = adata.obs['total_counts'] >= min_counts
            filters.append(filter_min_counts)
            logger.info(f"Min counts filter: {filter_min_counts.sum()} cells pass")
            
        if max_counts is not None:
            filter_max_counts = adata.obs['total_counts'] <= max_counts
            filters.append(filter_max_counts)
            logger.info(f"Max counts filter: {filter_max_counts.sum()} cells pass")
            
        if max_pct_mt is not None and 'pct_counts_mt' in adata.obs.columns:
            filter_mt = adata.obs['pct_counts_mt'] <= max_pct_mt
            filters.append(filter_mt)
            logger.info(f"MT filter: {filter_mt.sum()} cells pass")
            
        if max_pct_ribo is not None and 'pct_counts_ribo' in adata.obs.columns:
            filter_ribo = adata.obs['pct_counts_ribo'] <= max_pct_ribo
            filters.append(filter_ribo)
            logger.info(f"Ribosomal filter: {filter_ribo.sum()} cells pass")
            
        if max_doublet_score is not None and 'doublet_score' in adata.obs.columns:
            filter_doublet = adata.obs['doublet_score'] <= max_doublet_score
            filters.append(filter_doublet)
            logger.info(f"Doublet filter: {filter_doublet.sum()} cells pass")
            
        # Combine all filters
        if filters:
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter & f
                
            adata = adata[combined_filter, :]
            
        n_cells_filtered = adata.n_obs
        n_cells_removed = n_cells_orig - n_cells_filtered
        
        # Store filter statistics
        self.filter_stats['cells'] = {
            'original': n_cells_orig,
            'filtered': n_cells_filtered,
            'removed': n_cells_removed,
            'fraction_kept': n_cells_filtered / n_cells_orig if n_cells_orig > 0 else 0
        }
        
        logger.info(f"Cell filtering complete: {n_cells_filtered} cells kept, {n_cells_removed} removed")
        
        return adata
        
    def filter_genes(self, adata=None, min_cells=3, max_cells=None, 
                    min_counts=None, max_counts=None):
        """
        Filter genes based on expression criteria
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        min_cells : int
            Minimum number of cells expressing the gene
        max_cells : int, optional
            Maximum number of cells expressing the gene
        min_counts : int, optional
            Minimum total counts for the gene
        max_counts : int, optional
            Maximum total counts for the gene
            
        Returns:
        --------
        anndata.AnnData : Filtered data
        """
        if adata is None:
            adata = self.adata.copy()
        else:
            adata = adata.copy()
            
        logger.info("Filtering genes based on expression criteria...")
        
        # Store original counts
        n_genes_orig = adata.n_vars
        
        # Apply filters
        filters = []
        
        if min_cells is not None:
            filter_min_cells = adata.var['n_cells_by_counts'] >= min_cells
            filters.append(filter_min_cells)
            logger.info(f"Min cells filter: {filter_min_cells.sum()} genes pass")
            
        if max_cells is not None:
            filter_max_cells = adata.var['n_cells_by_counts'] <= max_cells
            filters.append(filter_max_cells)
            logger.info(f"Max cells filter: {filter_max_cells.sum()} genes pass")
            
        if min_counts is not None:
            filter_min_counts = adata.var['total_counts'] >= min_counts
            filters.append(filter_min_counts)
            logger.info(f"Min counts filter: {filter_min_counts.sum()} genes pass")
            
        if max_counts is not None:
            filter_max_counts = adata.var['total_counts'] <= max_counts
            filters.append(filter_max_counts)
            logger.info(f"Max counts filter: {filter_max_counts.sum()} genes pass")
            
        # Combine all filters
        if filters:
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter & f
                
            adata = adata[:, combined_filter]
            
        n_genes_filtered = adata.n_vars
        n_genes_removed = n_genes_orig - n_genes_filtered
        
        # Store filter statistics
        self.filter_stats['genes'] = {
            'original': n_genes_orig,
            'filtered': n_genes_filtered,
            'removed': n_genes_removed,
            'fraction_kept': n_genes_filtered / n_genes_orig if n_genes_orig > 0 else 0
        }
        
        logger.info(f"Gene filtering complete: {n_genes_filtered} genes kept, {n_genes_removed} removed")
        
        return adata
        
    def get_filter_summary(self):
        """Get summary of filtering results"""
        return self.filter_stats
        
    def get_qc_summary(self):
        """Get summary of QC metrics"""
        return self.qc_metrics


def calculate_qc_metrics(adata, mitochondrial_prefix='MT-', 
                        ribosomal_prefix='RP', hemoglobin_prefix='HB'):
    """
    Convenience function to calculate QC metrics
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    mitochondrial_prefix : str
        Prefix for mitochondrial genes
    ribosomal_prefix : str
        Prefix for ribosomal genes
    hemoglobin_prefix : str
        Prefix for hemoglobin genes
        
    Returns:
    --------
    dict : QC metrics
    """
    qc = QualityControl(adata)
    return qc.calculate_qc_metrics(mitochondrial_prefix=mitochondrial_prefix,
                                 ribosomal_prefix=ribosomal_prefix,
                                 hemoglobin_prefix=hemoglobin_prefix)


def filter_cells(adata, min_genes=200, max_genes=None, 
                min_counts=None, max_counts=None, max_pct_mt=20,
                max_pct_ribo=None, max_doublet_score=None):
    """
    Convenience function to filter cells based on QC metrics
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    min_genes : int
        Minimum number of genes per cell
    max_genes : int, optional
        Maximum number of genes per cell
    min_counts : int, optional
        Minimum total counts per cell
    max_counts : int, optional
        Maximum total counts per cell
    max_pct_mt : float
        Maximum percentage of mitochondrial genes
    max_pct_ribo : float, optional
        Maximum percentage of ribosomal genes
    max_doublet_score : float, optional
        Maximum doublet score
        
    Returns:
    --------
    anndata.AnnData : Filtered data
    """
    qc = QualityControl(adata)
    # First calculate QC metrics if not already done
    if 'total_counts' not in adata.obs.columns:
        qc.calculate_qc_metrics()
    return qc.filter_cells(min_genes=min_genes, max_genes=max_genes,
                          min_counts=min_counts, max_counts=max_counts,
                          max_pct_mt=max_pct_mt, max_pct_ribo=max_pct_ribo,
                          max_doublet_score=max_doublet_score)


def filter_genes(adata, min_cells=3, max_cells=None, 
                min_counts=None, max_counts=None):
    """
    Convenience function to filter genes based on expression criteria
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    min_cells : int
        Minimum number of cells expressing the gene
    max_cells : int, optional
        Maximum number of cells expressing the gene
    min_counts : int, optional
        Minimum total counts for the gene
    max_counts : int, optional
        Maximum total counts for the gene
        
    Returns:
    --------
    anndata.AnnData : Filtered data
    """
    qc = QualityControl(adata)
    return qc.filter_genes(min_cells=min_cells, max_cells=max_cells,
                          min_counts=min_counts, max_counts=max_counts) 