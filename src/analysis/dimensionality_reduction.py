"""
Dimensionality Reduction Module for Single Cell Analysis

This module provides various dimensionality reduction methods including
PCA, UMAP, t-SNE, and other techniques commonly used in single cell analysis.
"""

import numpy as np
import pandas as pd
import scanpy as sc
from typing import Dict, List, Optional, Tuple, Union
import logging
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DimensionalityReducer:
    """
    Comprehensive dimensionality reduction for single cell data
    
    This class provides methods for PCA, UMAP, t-SNE, and other
    dimensionality reduction techniques.
    """
    
    def __init__(self, adata=None):
        """
        Initialize DimensionalityReducer
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        """
        self.adata = adata
        self.reduction_history = []
        
    def run_pca(self, adata=None, n_comps=50, zero_center=True, 
                svd_solver='arpack', random_state=42, copy=False):
        """
        Principal Component Analysis (PCA)
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        n_comps : int
            Number of principal components to compute
        zero_center : bool
            Whether to center the data
        svd_solver : str
            SVD solver to use ('arpack', 'randomized', 'auto')
        random_state : int
            Random state for reproducibility
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Data with PCA results if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if adata is None:
            raise ValueError("No data provided for PCA")
            
        if copy:
            adata = adata.copy()
            
        logger.info(f"Running PCA with {n_comps} components")
        
        # Run PCA using scanpy
        sc.tl.pca(adata, n_comps=n_comps, zero_center=zero_center, 
                 svd_solver=svd_solver, random_state=random_state)
        
        # Calculate variance ratio
        variance_ratio = adata.uns['pca']['variance_ratio']
        cumulative_variance = np.cumsum(variance_ratio)
        
        # Record reduction
        self.reduction_history.append({
            'method': 'pca',
            'n_components': n_comps,
            'variance_explained': variance_ratio[:10].tolist(),  # First 10 PCs
            'cumulative_variance': cumulative_variance[:10].tolist(),
            'total_variance_explained': cumulative_variance[n_comps-1] if n_comps <= len(cumulative_variance) else cumulative_variance[-1]
        })
        
        logger.info(f"PCA completed. Variance explained by first 10 PCs: {variance_ratio[:10].sum():.3f}")
        
        if copy:
            return adata
            
    def run_umap(self, adata=None, n_neighbors=15, n_components=2, metric='euclidean',
                min_dist=0.5, spread=1.0, random_state=42, use_rep='X_pca', copy=False):
        """
        Uniform Manifold Approximation and Projection (UMAP)
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        n_neighbors : int
            Number of neighbors for UMAP
        n_components : int
            Number of dimensions for UMAP embedding
        metric : str
            Distance metric for UMAP
        min_dist : float
            Minimum distance parameter for UMAP
        spread : float
            Effective scale of embedded points
        random_state : int
            Random state for reproducibility
        use_rep : str
            Representation to use ('X_pca', 'X', or other)
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Data with UMAP results if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if copy:
            adata = adata.copy()
            
        logger.info(f"Running UMAP with {n_neighbors} neighbors, {n_components} components")
        
        # Check if PCA has been run if using X_pca
        if use_rep == 'X_pca' and 'X_pca' not in adata.obsm:
            logger.info("PCA not found, running PCA first...")
            self.run_pca(adata, copy=False)
            
        # Compute neighbors first
        sc.pp.neighbors(adata, n_neighbors=n_neighbors, use_rep=use_rep, 
                       metric=metric, random_state=random_state)
        
        # Run UMAP
        sc.tl.umap(adata, min_dist=min_dist, spread=spread, 
                  n_components=n_components, random_state=random_state)
        
        # Record reduction
        self.reduction_history.append({
            'method': 'umap',
            'n_neighbors': n_neighbors,
            'n_components': n_components,
            'metric': metric,
            'min_dist': min_dist,
            'spread': spread,
            'use_rep': use_rep
        })
        
        logger.info("UMAP completed")
        
        if copy:
            return adata
            
    def run_tsne(self, adata=None, n_components=2, perplexity=30, early_exaggeration=12,
                learning_rate=1000, n_iter=1000, random_state=42, use_rep='X_pca', copy=False):
        """
        t-distributed Stochastic Neighbor Embedding (t-SNE)
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        n_components : int
            Number of dimensions for t-SNE embedding
        perplexity : float
            Perplexity parameter for t-SNE
        early_exaggeration : float
            Early exaggeration factor
        learning_rate : float
            Learning rate for t-SNE
        n_iter : int
            Number of iterations
        random_state : int
            Random state for reproducibility
        use_rep : str
            Representation to use ('X_pca', 'X', or other)
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Data with t-SNE results if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if copy:
            adata = adata.copy()
            
        logger.info(f"Running t-SNE with perplexity {perplexity}, {n_components} components")
        
        # Check if PCA has been run if using X_pca
        if use_rep == 'X_pca' and 'X_pca' not in adata.obsm:
            logger.info("PCA not found, running PCA first...")
            self.run_pca(adata, copy=False)
            
        # Run t-SNE using scanpy
        sc.tl.tsne(adata, n_components=n_components, perplexity=perplexity,
                  early_exaggeration=early_exaggeration, learning_rate=learning_rate,
                  n_iter=n_iter, random_state=random_state, use_rep=use_rep)
        
        # Record reduction
        self.reduction_history.append({
            'method': 'tsne',
            'n_components': n_components,
            'perplexity': perplexity,
            'early_exaggeration': early_exaggeration,
            'learning_rate': learning_rate,
            'n_iter': n_iter,
            'use_rep': use_rep
        })
        
        logger.info("t-SNE completed")
        
        if copy:
            return adata
            
    def run_diffusion_map(self, adata=None, n_comps=15, n_neighbors=30, 
                         random_state=42, copy=False):
        """
        Diffusion Map embedding
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        n_comps : int
            Number of diffusion components
        n_neighbors : int
            Number of neighbors for graph construction
        random_state : int
            Random state for reproducibility
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Data with diffusion map results if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if copy:
            adata = adata.copy()
            
        logger.info(f"Running Diffusion Map with {n_comps} components")
        
        # Compute neighbors if not already done
        if 'neighbors' not in adata.uns:
            sc.pp.neighbors(adata, n_neighbors=n_neighbors, random_state=random_state)
            
        # Run diffusion map
        sc.tl.diffmap(adata, n_comps=n_comps)
        
        # Record reduction
        self.reduction_history.append({
            'method': 'diffusion_map',
            'n_components': n_comps,
            'n_neighbors': n_neighbors
        })
        
        logger.info("Diffusion Map completed")
        
        if copy:
            return adata
            
    def run_force_atlas2(self, adata=None, iterations=500, pos_init=None,
                        random_state=42, copy=False):
        """
        Force-directed graph layout (ForceAtlas2)
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        iterations : int
            Number of iterations
        pos_init : str, optional
            Initial positions ('paga', 'umap', 'random')
        random_state : int
            Random state for reproducibility
        copy : bool
            Return a copy instead of modifying in place
            
        Returns:
        --------
        anndata.AnnData or None : Data with ForceAtlas2 results if copy=True
        """
        if adata is None:
            adata = self.adata
            
        if copy:
            adata = adata.copy()
            
        logger.info(f"Running ForceAtlas2 with {iterations} iterations")
        
        # Compute neighbors if not already done
        if 'neighbors' not in adata.uns:
            sc.pp.neighbors(adata, random_state=random_state)
            
        try:
            # Run ForceAtlas2
            sc.tl.draw_graph(adata, layout='fa', iterations=iterations, 
                           pos_init=pos_init, random_state=random_state)
            
            # Record reduction
            self.reduction_history.append({
                'method': 'force_atlas2',
                'iterations': iterations,
                'pos_init': pos_init
            })
            
            logger.info("ForceAtlas2 completed")
            
        except Exception as e:
            logger.error(f"ForceAtlas2 failed: {e}")
            logger.info("Falling back to spring layout")
            
            # Fallback to spring layout
            sc.tl.draw_graph(adata, layout='spring', iterations=iterations,
                           random_state=random_state)
            
            self.reduction_history.append({
                'method': 'spring_layout',
                'iterations': iterations
            })
            
        if copy:
            return adata
            
    def find_optimal_pca_components(self, adata=None, max_components=100, 
                                  variance_threshold=0.95):
        """
        Find optimal number of PCA components based on variance explained
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        max_components : int
            Maximum number of components to test
        variance_threshold : float
            Cumulative variance threshold
            
        Returns:
        --------
        dict : Optimal component analysis results
        """
        if adata is None:
            adata = self.adata
            
        logger.info(f"Finding optimal PCA components (max: {max_components}, threshold: {variance_threshold})")
        
        # Run PCA with max components
        temp_adata = adata.copy()
        sc.tl.pca(temp_adata, n_comps=min(max_components, temp_adata.n_vars-1))
        
        variance_ratio = temp_adata.uns['pca']['variance_ratio']
        cumulative_variance = np.cumsum(variance_ratio)
        
        # Find elbow point using second derivative
        second_derivative = np.diff(variance_ratio, 2)
        elbow_point = np.argmax(second_derivative) + 2  # +2 due to double diff
        
        # Find threshold point
        threshold_point = np.argmax(cumulative_variance >= variance_threshold) + 1
        
        results = {
            'variance_ratio': variance_ratio.tolist(),
            'cumulative_variance': cumulative_variance.tolist(),
            'elbow_point': int(elbow_point),
            'threshold_point': int(threshold_point),
            'recommended_components': int(min(elbow_point, threshold_point)),
            'variance_at_elbow': float(cumulative_variance[elbow_point-1]),
            'variance_at_threshold': float(cumulative_variance[threshold_point-1])
        }
        
        logger.info(f"Recommended PCA components: {results['recommended_components']}")
        
        return results
        
    def optimize_umap_parameters(self, adata=None, n_neighbors_range=(5, 50), 
                                min_dist_range=(0.1, 1.0), n_trials=10):
        """
        Optimize UMAP parameters using grid search
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        n_neighbors_range : tuple
            Range of n_neighbors to test
        min_dist_range : tuple
            Range of min_dist to test
        n_trials : int
            Number of parameter combinations to test
            
        Returns:
        --------
        dict : Optimization results
        """
        if adata is None:
            adata = self.adata
            
        logger.info("Optimizing UMAP parameters...")
        
        # Generate parameter combinations
        n_neighbors_values = np.linspace(n_neighbors_range[0], n_neighbors_range[1], 
                                       int(np.sqrt(n_trials))).astype(int)
        min_dist_values = np.linspace(min_dist_range[0], min_dist_range[1], 
                                    int(np.sqrt(n_trials)))
        
        results = []
        
        for n_neighbors in n_neighbors_values:
            for min_dist in min_dist_values:
                try:
                    # Test parameters
                    temp_adata = adata.copy()
                    self.run_umap(temp_adata, n_neighbors=int(n_neighbors), 
                                min_dist=min_dist, copy=False)
                    
                    # Calculate quality metrics (simplified)
                    # In practice, you might use more sophisticated metrics
                    embedding = temp_adata.obsm['X_umap']
                    spread = np.std(embedding, axis=0).mean()
                    
                    results.append({
                        'n_neighbors': int(n_neighbors),
                        'min_dist': float(min_dist),
                        'spread': float(spread)
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed for n_neighbors={n_neighbors}, min_dist={min_dist}: {e}")
                    
        if results:
            # Find best parameters (highest spread, indicating good separation)
            best_result = max(results, key=lambda x: x['spread'])
            
            optimization_results = {
                'best_parameters': best_result,
                'all_results': results,
                'n_trials_completed': len(results)
            }
            
            logger.info(f"Best UMAP parameters: n_neighbors={best_result['n_neighbors']}, "
                       f"min_dist={best_result['min_dist']}")
            
            return optimization_results
        else:
            logger.error("No successful parameter combinations found")
            return None
            
    def get_reduction_summary(self):
        """Get summary of dimensionality reductions performed"""
        return self.reduction_history
        
    def plot_pca_variance(self, adata=None, n_components=50):
        """
        Plot PCA variance explained
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        n_components : int
            Number of components to plot
        """
        if adata is None:
            adata = self.adata
            
        if 'pca' not in adata.uns:
            logger.warning("PCA not found, running PCA first...")
            self.run_pca(adata, n_comps=n_components)
            
        # This would create a plot - implementation depends on GUI integration
        variance_ratio = adata.uns['pca']['variance_ratio'][:n_components]
        cumulative_variance = np.cumsum(variance_ratio)
        
        return {
            'variance_ratio': variance_ratio.tolist(),
            'cumulative_variance': cumulative_variance.tolist(),
            'components': list(range(1, len(variance_ratio) + 1))
        }


def run_pca(adata, n_comps=50, zero_center=True, random_state=42, copy=False):
    """
    Convenience function for PCA
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    n_comps : int
        Number of components
    zero_center : bool
        Whether to center the data
    random_state : int
        Random state for reproducibility
    copy : bool
        Return a copy instead of modifying in place
        
    Returns:
    --------
    anndata.AnnData or None : Data with PCA results if copy=True
    """
    reducer = DimensionalityReducer(adata)
    return reducer.run_pca(n_comps=n_comps, zero_center=zero_center, 
                          random_state=random_state, copy=copy)


def run_umap(adata, n_neighbors=15, min_dist=0.5, random_state=42, copy=False):
    """
    Convenience function for UMAP
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    n_neighbors : int
        Number of neighbors
    min_dist : float
        Minimum distance parameter
    random_state : int
        Random state for reproducibility
    copy : bool
        Return a copy instead of modifying in place
        
    Returns:
    --------
    anndata.AnnData or None : Data with UMAP results if copy=True
    """
    reducer = DimensionalityReducer(adata)
    return reducer.run_umap(n_neighbors=n_neighbors, min_dist=min_dist, 
                           random_state=random_state, copy=copy)


def run_tsne(adata, perplexity=30, random_state=42, copy=False):
    """
    Convenience function for t-SNE
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    perplexity : float
        Perplexity parameter
    random_state : int
        Random state for reproducibility
    copy : bool
        Return a copy instead of modifying in place
        
    Returns:
    --------
    anndata.AnnData or None : Data with t-SNE results if copy=True
    """
    reducer = DimensionalityReducer(adata)
    return reducer.run_tsne(perplexity=perplexity, random_state=random_state, copy=copy) 