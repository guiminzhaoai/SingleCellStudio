"""
Clustering Module for Single Cell Analysis

This module provides clustering algorithms commonly used in single cell analysis
including Leiden and Louvain clustering.
"""

import numpy as np
import pandas as pd
import scanpy as sc
from typing import Dict, List, Optional, Tuple, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClusterAnalyzer:
    """
    Comprehensive clustering for single cell data
    
    This class provides methods for Leiden and Louvain clustering
    with parameter optimization and cluster evaluation.
    """
    
    def __init__(self, adata=None):
        """
        Initialize ClusterAnalyzer
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        """
        self.adata = adata
        self.clustering_history = []
        
    def leiden_clustering(self, adata=None, resolution=0.5, random_state=42, 
                         key_added='leiden', copy=False):
        """
        Leiden clustering algorithm
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        resolution : float
            Resolution parameter for clustering
        random_state : int
            Random state for reproducibility
        key_added : str
            Key to store clustering results
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Data with clustering results if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if copy:
            adata = adata.copy()
            
        logger.info(f"Running Leiden clustering with resolution {resolution}")
        
        # Check if neighbors have been computed
        if 'neighbors' not in adata.uns:
            logger.info("Computing neighbors first...")
            sc.pp.neighbors(adata, random_state=random_state)
            
        # Run Leiden clustering
        sc.tl.leiden(adata, resolution=resolution, random_state=random_state, 
                    key_added=key_added)
        
        # Get cluster statistics
        n_clusters = len(adata.obs[key_added].unique())
        cluster_sizes = adata.obs[key_added].value_counts().sort_index()
        
        # Record clustering
        self.clustering_history.append({
            'method': 'leiden',
            'resolution': resolution,
            'n_clusters': n_clusters,
            'cluster_sizes': cluster_sizes.tolist(),
            'key_added': key_added
        })
        
        logger.info(f"Leiden clustering completed: {n_clusters} clusters found")
        
        if copy:
            return adata
            
    def louvain_clustering(self, adata=None, resolution=0.5, random_state=42,
                          key_added='louvain', copy=False):
        """
        Louvain clustering algorithm
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        resolution : float
            Resolution parameter for clustering
        random_state : int
            Random state for reproducibility
        key_added : str
            Key to store clustering results
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Data with clustering results if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if copy:
            adata = adata.copy()
            
        logger.info(f"Running Louvain clustering with resolution {resolution}")
        
        # Check if neighbors have been computed
        if 'neighbors' not in adata.uns:
            logger.info("Computing neighbors first...")
            sc.pp.neighbors(adata, random_state=random_state)
            
        # Run Louvain clustering
        sc.tl.louvain(adata, resolution=resolution, random_state=random_state,
                     key_added=key_added)
        
        # Get cluster statistics
        n_clusters = len(adata.obs[key_added].unique())
        cluster_sizes = adata.obs[key_added].value_counts().sort_index()
        
        # Record clustering
        self.clustering_history.append({
            'method': 'louvain',
            'resolution': resolution,
            'n_clusters': n_clusters,
            'cluster_sizes': cluster_sizes.tolist(),
            'key_added': key_added
        })
        
        logger.info(f"Louvain clustering completed: {n_clusters} clusters found")
        
        if copy:
            return adata
            
    def optimize_resolution(self, adata=None, method='leiden', 
                           resolution_range=(0.1, 2.0), n_steps=10):
        """
        Optimize clustering resolution parameter
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        method : str
            Clustering method ('leiden' or 'louvain')
        resolution_range : tuple
            Range of resolutions to test
        n_steps : int
            Number of resolution values to test
            
        Returns:
        --------
        dict : Optimization results
        """
        if adata is None:
            adata = self.adata
            
        logger.info(f"Optimizing {method} resolution...")
        
        resolutions = np.linspace(resolution_range[0], resolution_range[1], n_steps)
        results = []
        
        for res in resolutions:
            temp_adata = adata.copy()
            
            if method == 'leiden':
                self.leiden_clustering(temp_adata, resolution=res, copy=False)
                cluster_key = 'leiden'
            else:
                self.louvain_clustering(temp_adata, resolution=res, copy=False)
                cluster_key = 'louvain'
                
            n_clusters = len(temp_adata.obs[cluster_key].unique())
            
            # Calculate silhouette score (simplified)
            if 'X_pca' in temp_adata.obsm:
                from sklearn.metrics import silhouette_score
                try:
                    sil_score = silhouette_score(temp_adata.obsm['X_pca'], 
                                               temp_adata.obs[cluster_key].astype(str))
                except:
                    sil_score = 0.0
            else:
                sil_score = 0.0
                
            results.append({
                'resolution': float(res),
                'n_clusters': n_clusters,
                'silhouette_score': float(sil_score)
            })
            
        # Find best resolution (highest silhouette score)
        if results:
            best_result = max(results, key=lambda x: x['silhouette_score'])
            
            optimization_results = {
                'method': method,
                'best_resolution': best_result['resolution'],
                'best_n_clusters': best_result['n_clusters'],
                'best_silhouette_score': best_result['silhouette_score'],
                'all_results': results
            }
            
            logger.info(f"Best {method} resolution: {best_result['resolution']} "
                       f"({best_result['n_clusters']} clusters)")
            
            return optimization_results
        else:
            return None
            
    def get_clustering_summary(self):
        """Get summary of clustering results"""
        return self.clustering_history


def run_leiden_clustering(adata, resolution=0.5, random_state=42, copy=False):
    """
    Convenience function for Leiden clustering
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    resolution : float
        Resolution parameter
    random_state : int
        Random state for reproducibility
    copy : bool
        Return a copy instead of modifying in place
        
    Returns:
    --------
    anndata.AnnData or None : Data with clustering results if copy=True
    """
    analyzer = ClusterAnalyzer(adata)
    return analyzer.leiden_clustering(resolution=resolution, random_state=random_state, copy=copy)


def run_louvain_clustering(adata, resolution=0.5, random_state=42, copy=False):
    """
    Convenience function for Louvain clustering
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    resolution : float
        Resolution parameter
    random_state : int
        Random state for reproducibility
    copy : bool
        Return a copy instead of modifying in place
        
    Returns:
    --------
    anndata.AnnData or None : Data with clustering results if copy=True
    """
    analyzer = ClusterAnalyzer(adata)
    return analyzer.louvain_clustering(resolution=resolution, random_state=random_state, copy=copy)


def compute_neighbors(adata, n_neighbors=15, n_pcs=None, use_rep=None, 
                     knn=True, random_state=42, method='umap', metric='euclidean'):
    """
    Convenience function to compute neighborhood graph
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    n_neighbors : int
        Number of neighbors for each cell
    n_pcs : int, optional
        Number of PCs to use (default: use all available)
    use_rep : str, optional
        Representation to use ('X_pca', 'X_umap', etc.)
    knn : bool
        Whether to use k-nearest neighbors (True) or radius-based (False)
    random_state : int
        Random state for reproducibility
    method : str
        Method for computing neighbors ('umap' or 'gauss')
    metric : str
        Distance metric to use
        
    Returns:
    --------
    None : Modifies adata in place
    """
    logger.info(f"Computing neighborhood graph with {n_neighbors} neighbors")
    
    # Use scanpy's neighbors function
    sc.pp.neighbors(adata, 
                   n_neighbors=n_neighbors,
                   n_pcs=n_pcs,
                   use_rep=use_rep,
                   knn=knn,
                   random_state=random_state,
                   method=method,
                   metric=metric)
    
    logger.info("Neighborhood graph computation completed") 