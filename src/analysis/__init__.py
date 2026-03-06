"""
Analysis package for SingleCellStudio

This package provides comprehensive single cell RNA-seq analysis capabilities
including quality control, normalization, dimensionality reduction, and clustering.
"""

from .quality_control import QualityControl, calculate_qc_metrics, filter_cells, filter_genes
from .normalization import Normalizer, normalize_data, log_normalize, scale_data
from .dimensionality_reduction import DimensionalityReducer, run_pca, run_umap, run_tsne
from .clustering import ClusterAnalyzer, run_leiden_clustering, run_louvain_clustering, compute_neighbors
from .pipeline import AnalysisPipeline, StandardPipeline, run_standard_pipeline, find_variable_genes

__all__ = [
    # Quality Control
    'QualityControl',
    'calculate_qc_metrics',
    'filter_cells',
    'filter_genes',
    
    # Normalization
    'Normalizer', 
    'normalize_data',
    'log_normalize',
    'scale_data',
    
    # Feature Selection
    'find_variable_genes',
    
    # Dimensionality Reduction
    'DimensionalityReducer',
    'run_pca',
    'run_umap', 
    'run_tsne',
    
    # Clustering
    'ClusterAnalyzer',
    'run_leiden_clustering',
    'run_louvain_clustering',
    'compute_neighbors',
    
    # Pipeline Management
    'AnalysisPipeline',
    'StandardPipeline',
    'run_standard_pipeline'
]

# Version info
__version__ = "0.2.0"
__author__ = "SingleCellStudio Team" 