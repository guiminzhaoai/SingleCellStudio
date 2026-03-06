"""
SingleCellStudio Visualization Package

This package contains visualization functions for single cell analysis results.
"""

from .plots import (
    create_umap_plot, create_pca_plot, create_qc_plots, 
    create_cluster_plot, create_heatmap, create_violin_plots
)
from .interactive import create_interactive_umap, create_interactive_plots
from .matplotlib_backend import MatplotlibPlotter

__all__ = [
    'create_umap_plot', 'create_pca_plot', 'create_qc_plots',
    'create_cluster_plot', 'create_heatmap', 'create_violin_plots',
    'create_interactive_umap', 'create_interactive_plots',
    'MatplotlibPlotter'
] 