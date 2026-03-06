"""
SingleCellStudio Plotting Functions

Core plotting functions for single cell analysis visualization.
"""

import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap
import seaborn as sns
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

try:
    import anndata as ad
    import scanpy as sc
    SCANPY_AVAILABLE = True
except ImportError:
    SCANPY_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Set up plotting style
plt.style.use('default')
sns.set_palette("husl")

def create_umap_plot(adata: ad.AnnData, 
                    color_by: str = 'leiden',
                    title: Optional[str] = None,
                    figsize: Tuple[int, int] = (8, 6),
                    save_path: Optional[str] = None,
                    show_legend: bool = True,
                    point_size: float = 1.0) -> plt.Figure:
    """
    Create UMAP scatter plot
    
    Args:
        adata: AnnData object with UMAP coordinates
        color_by: Column name to color points by
        title: Plot title
        figsize: Figure size
        save_path: Path to save figure
        show_legend: Whether to show legend
        point_size: Size of scatter points
        
    Returns:
        matplotlib Figure object
    """
    if 'X_umap' not in adata.obsm:
        raise ValueError("UMAP coordinates not found. Run UMAP first.")
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Get UMAP coordinates
    umap_coords = adata.obsm['X_umap']
    
    # Get colors
    if color_by in adata.obs.columns:
        colors = adata.obs[color_by]
        
        # Handle categorical vs continuous data
        if pd.api.types.is_categorical_dtype(colors) or colors.dtype == 'object':
            # Categorical coloring
            unique_vals = colors.unique()
            n_colors = len(unique_vals)
            
            # Use a nice color palette
            if n_colors <= 10:
                palette = sns.color_palette("tab10", n_colors)
            elif n_colors <= 20:
                palette = sns.color_palette("tab20", n_colors)
            else:
                palette = sns.color_palette("husl", n_colors)
            
            color_map = dict(zip(unique_vals, palette))
            
            # Plot each category separately for legend
            for i, val in enumerate(unique_vals):
                mask = colors == val
                ax.scatter(umap_coords[mask, 0], umap_coords[mask, 1], 
                          c=[color_map[val]], s=point_size, alpha=0.7,
                          label=str(val), edgecolors='none')
            
            if show_legend and n_colors <= 30:
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
                         frameon=False, markerscale=2)
        else:
            # Continuous coloring
            scatter = ax.scatter(umap_coords[:, 0], umap_coords[:, 1], 
                               c=colors, s=point_size, alpha=0.7,
                               cmap='viridis', edgecolors='none')
            if show_legend:
                plt.colorbar(scatter, ax=ax, label=color_by)
    else:
        # Default coloring
        ax.scatter(umap_coords[:, 0], umap_coords[:, 1], 
                  s=point_size, alpha=0.7, c='#1f77b4', edgecolors='none')
    
    # Formatting
    ax.set_xlabel('UMAP 1')
    ax.set_ylabel('UMAP 2')
    ax.set_title(title or f'UMAP colored by {color_by}')
    ax.grid(True, alpha=0.3)
    
    # Remove ticks for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def create_pca_plot(adata: ad.AnnData,
                   components: Tuple[int, int] = (1, 2),
                   color_by: str = 'leiden',
                   title: Optional[str] = None,
                   figsize: Tuple[int, int] = (8, 6),
                   save_path: Optional[str] = None,
                   show_variance: bool = True) -> plt.Figure:
    """
    Create PCA scatter plot
    
    Args:
        adata: AnnData object with PCA coordinates
        components: Which PC components to plot (1-indexed)
        color_by: Column name to color points by
        title: Plot title
        figsize: Figure size
        save_path: Path to save figure
        show_variance: Whether to show variance explained in labels
        
    Returns:
        matplotlib Figure object
    """
    if 'X_pca' not in adata.obsm:
        raise ValueError("PCA coordinates not found. Run PCA first.")
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Get PCA coordinates (convert to 0-indexed)
    pc1_idx, pc2_idx = components[0] - 1, components[1] - 1
    pca_coords = adata.obsm['X_pca'][:, [pc1_idx, pc2_idx]]
    
    # Get variance explained if available
    variance_ratio = None
    if 'pca' in adata.uns and 'variance_ratio' in adata.uns['pca']:
        variance_ratio = adata.uns['pca']['variance_ratio']
    
    # Color by specified column
    if color_by in adata.obs.columns:
        colors = adata.obs[color_by]
        
        if pd.api.types.is_categorical_dtype(colors) or colors.dtype == 'object':
            # Categorical coloring
            unique_vals = colors.unique()
            n_colors = len(unique_vals)
            palette = sns.color_palette("tab10" if n_colors <= 10 else "husl", n_colors)
            color_map = dict(zip(unique_vals, palette))
            
            for val in unique_vals:
                mask = colors == val
                ax.scatter(pca_coords[mask, 0], pca_coords[mask, 1],
                          c=[color_map[val]], s=1.0, alpha=0.7,
                          label=str(val), edgecolors='none')
            
            if n_colors <= 20:
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False)
        else:
            # Continuous coloring
            scatter = ax.scatter(pca_coords[:, 0], pca_coords[:, 1],
                               c=colors, s=1.0, alpha=0.7,
                               cmap='viridis', edgecolors='none')
            plt.colorbar(scatter, ax=ax, label=color_by)
    else:
        ax.scatter(pca_coords[:, 0], pca_coords[:, 1],
                  s=1.0, alpha=0.7, c='#1f77b4', edgecolors='none')
    
    # Labels with variance explained
    if show_variance and variance_ratio is not None:
        xlabel = f'PC{components[0]} ({variance_ratio[pc1_idx]:.1%} variance)'
        ylabel = f'PC{components[1]} ({variance_ratio[pc2_idx]:.1%} variance)'
    else:
        xlabel = f'PC{components[0]}'
        ylabel = f'PC{components[1]}'
    
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title or f'PCA colored by {color_by}')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def create_qc_plots(adata: ad.AnnData,
                   figsize: Tuple[int, int] = (15, 5),
                   save_path: Optional[str] = None) -> plt.Figure:
    """
    Create quality control plots
    
    Args:
        adata: AnnData object with QC metrics
        figsize: Figure size
        save_path: Path to save figure
        
    Returns:
        matplotlib Figure object
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    
    # Plot 1: Number of genes per cell
    if 'n_genes_by_counts' in adata.obs.columns:
        data = adata.obs['n_genes_by_counts'].dropna()
        if len(data) > 0:
            axes[0].hist(data, bins=50, alpha=0.7, color='skyblue')
            axes[0].set_xlabel('Number of genes')
            axes[0].set_ylabel('Number of cells')
            axes[0].set_title('Genes per cell')
            axes[0].grid(True, alpha=0.3)
        else:
            axes[0].text(0.5, 0.5, 'No data available', ha='center', va='center', transform=axes[0].transAxes)
            axes[0].set_title('Genes per cell - No data')
    
    # Plot 2: Total counts per cell
    if 'total_counts' in adata.obs.columns:
        data = adata.obs['total_counts'].dropna()
        if len(data) > 0:
            axes[1].hist(data, bins=50, alpha=0.7, color='lightgreen')
            axes[1].set_xlabel('Total counts')
            axes[1].set_ylabel('Number of cells')
            axes[1].set_title('Total counts per cell')
            axes[1].grid(True, alpha=0.3)
        else:
            axes[1].text(0.5, 0.5, 'No data available', ha='center', va='center', transform=axes[1].transAxes)
            axes[1].set_title('Total counts per cell - No data')
    
    # Plot 3: Mitochondrial gene percentage
    if 'pct_counts_mt' in adata.obs.columns:
        data = adata.obs['pct_counts_mt'].dropna()
        if len(data) > 0:
            axes[2].hist(data, bins=50, alpha=0.7, color='salmon')
            axes[2].set_xlabel('Mitochondrial gene %')
            axes[2].set_ylabel('Number of cells')
            axes[2].set_title('Mitochondrial gene percentage')
            axes[2].grid(True, alpha=0.3)
        else:
            axes[2].text(0.5, 0.5, 'No data available', ha='center', va='center', transform=axes[2].transAxes)
            axes[2].set_title('Mitochondrial gene percentage - No data')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def create_cluster_plot(adata: ad.AnnData,
                       cluster_key: str = 'leiden',
                       figsize: Tuple[int, int] = (10, 8),
                       save_path: Optional[str] = None) -> plt.Figure:
    """
    Create cluster visualization with UMAP
    
    Args:
        adata: AnnData object
        cluster_key: Column name for cluster assignments
        figsize: Figure size
        save_path: Path to save figure
        
    Returns:
        matplotlib Figure object
    """
    if 'X_umap' not in adata.obsm:
        raise ValueError("UMAP coordinates not found. Run UMAP first.")
    
    if cluster_key not in adata.obs.columns:
        raise ValueError(f"Cluster key '{cluster_key}' not found in adata.obs")
    
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # Plot 1: UMAP with clusters
    umap_coords = adata.obsm['X_umap']
    clusters = adata.obs[cluster_key]
    unique_clusters = sorted(clusters.unique())
    n_clusters = len(unique_clusters)
    
    # Use appropriate color palette
    if n_clusters <= 10:
        palette = sns.color_palette("tab10", n_clusters)
    elif n_clusters <= 20:
        palette = sns.color_palette("tab20", n_clusters)
    else:
        palette = sns.color_palette("husl", n_clusters)
    
    color_map = dict(zip(unique_clusters, palette))
    
    for cluster in unique_clusters:
        mask = clusters == cluster
        axes[0].scatter(umap_coords[mask, 0], umap_coords[mask, 1],
                       c=[color_map[cluster]], s=1.0, alpha=0.7,
                       label=f'Cluster {cluster}', edgecolors='none')
    
    axes[0].set_xlabel('UMAP 1')
    axes[0].set_ylabel('UMAP 2')
    axes[0].set_title(f'Clusters (n={n_clusters})')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xticks([])
    axes[0].set_yticks([])
    
    if n_clusters <= 20:
        axes[0].legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False)
    
    # Plot 2: Cluster size bar plot
    cluster_counts = clusters.value_counts().sort_index()
    bars = axes[1].bar(range(len(cluster_counts)), cluster_counts.values, 
                      color=[color_map[c] for c in cluster_counts.index])
    
    axes[1].set_xlabel('Cluster')
    axes[1].set_ylabel('Number of cells')
    axes[1].set_title('Cluster sizes')
    axes[1].set_xticks(range(len(cluster_counts)))
    axes[1].set_xticklabels(cluster_counts.index)
    axes[1].grid(True, alpha=0.3, axis='y')
    
    # Add count labels on bars
    for i, (bar, count) in enumerate(zip(bars, cluster_counts.values)):
        axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + count*0.01,
                    str(count), ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def create_heatmap(adata: ad.AnnData,
                  genes: List[str],
                  group_by: str = 'leiden',
                  figsize: Tuple[int, int] = (10, 8),
                  save_path: Optional[str] = None,
                  show_gene_names: bool = True) -> plt.Figure:
    """
    Create expression heatmap
    
    Args:
        adata: AnnData object
        genes: List of genes to plot
        group_by: Column to group cells by
        figsize: Figure size
        save_path: Path to save figure
        show_gene_names: Whether to show gene names on y-axis
        
    Returns:
        matplotlib Figure object
    """
    # Find genes that exist in the data
    available_genes = [g for g in genes if g in adata.var_names]
    if not available_genes:
        raise ValueError("None of the specified genes found in data")
    
    if len(available_genes) < len(genes):
        missing = set(genes) - set(available_genes)
        logger.warning(f"Genes not found: {missing}")
    
    # Get expression data
    gene_indices = [list(adata.var_names).index(g) for g in available_genes]
    expr_data = adata.X[:, gene_indices]
    
    # Convert to dense if sparse
    if hasattr(expr_data, 'toarray'):
        expr_data = expr_data.toarray()
    
    # Create DataFrame
    expr_df = pd.DataFrame(expr_data, columns=available_genes, index=adata.obs_names)
    expr_df[group_by] = adata.obs[group_by].values
    
    # Group by cluster and calculate mean expression
    grouped = expr_df.groupby(group_by)[available_genes].mean()
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.heatmap(grouped.T, annot=True, fmt='.2f', cmap='viridis',
                ax=ax, cbar_kws={'label': 'Mean expression'})
    
    ax.set_xlabel(f'{group_by.title()}')
    ax.set_ylabel('Genes' if show_gene_names else '')
    ax.set_title(f'Gene expression by {group_by}')
    
    if not show_gene_names:
        ax.set_yticklabels([])
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def create_violin_plots(adata: ad.AnnData,
                       genes: List[str],
                       group_by: str = 'leiden',
                       figsize: Optional[Tuple[int, int]] = None,
                       save_path: Optional[str] = None) -> plt.Figure:
    """
    Create violin plots for gene expression
    
    Args:
        adata: AnnData object
        genes: List of genes to plot
        group_by: Column to group cells by
        figsize: Figure size
        save_path: Path to save figure
        
    Returns:
        matplotlib Figure object
    """
    # Find available genes
    available_genes = [g for g in genes if g in adata.var_names]
    if not available_genes:
        raise ValueError("None of the specified genes found in data")
    
    n_genes = len(available_genes)
    
    # Calculate figure size
    if figsize is None:
        figsize = (4 * n_genes, 6)
    
    fig, axes = plt.subplots(1, n_genes, figsize=figsize, squeeze=False)
    axes = axes.flatten()
    
    for i, gene in enumerate(available_genes):
        # Get gene expression
        gene_idx = list(adata.var_names).index(gene)
        expr = adata.X[:, gene_idx]
        
        if hasattr(expr, 'toarray'):
            expr = expr.toarray().flatten()
        
        # Create DataFrame for plotting
        plot_df = pd.DataFrame({
            'expression': expr,
            'group': adata.obs[group_by].values
        })
        
        # Create violin plot
        sns.violinplot(data=plot_df, x='group', y='expression', ax=axes[i])
        axes[i].set_title(gene)
        axes[i].set_xlabel(group_by.title())
        axes[i].set_ylabel('Expression')
        axes[i].grid(True, alpha=0.3)
        
        # Rotate x-axis labels if many groups
        if len(adata.obs[group_by].unique()) > 5:
            axes[i].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def create_summary_plot(adata: ad.AnnData,
                       figsize: Tuple[int, int] = (16, 12),
                       save_path: Optional[str] = None) -> plt.Figure:
    """
    Create comprehensive summary plot with multiple panels
    
    Args:
        adata: AnnData object with analysis results
        figsize: Figure size
        save_path: Path to save figure
        
    Returns:
        matplotlib Figure object
    """
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Panel 1: UMAP with clusters
    if 'X_umap' in adata.obsm and 'leiden' in adata.obs.columns:
        ax1 = fig.add_subplot(gs[0, 0])
        umap_coords = adata.obsm['X_umap']
        clusters = adata.obs['leiden']
        unique_clusters = sorted(clusters.unique())
        
        palette = sns.color_palette("tab10" if len(unique_clusters) <= 10 else "husl", 
                                   len(unique_clusters))
        color_map = dict(zip(unique_clusters, palette))
        
        for cluster in unique_clusters:
            mask = clusters == cluster
            ax1.scatter(umap_coords[mask, 0], umap_coords[mask, 1],
                       c=[color_map[cluster]], s=0.5, alpha=0.7, edgecolors='none')
        
        ax1.set_title('UMAP - Clusters')
        ax1.set_xticks([])
        ax1.set_yticks([])
    
    # Panel 2: QC metrics
    if 'n_genes_by_counts' in adata.obs.columns:
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.hist(adata.obs['n_genes_by_counts'], bins=30, alpha=0.7, color='skyblue')
        ax2.set_title('Genes per cell')
        ax2.set_xlabel('Number of genes')
        ax2.set_ylabel('Frequency')
    
    # Panel 3: Total counts
    if 'total_counts' in adata.obs.columns:
        ax3 = fig.add_subplot(gs[0, 2])
        ax3.hist(adata.obs['total_counts'], bins=30, alpha=0.7, color='lightgreen')
        ax3.set_title('Total counts per cell')
        ax3.set_xlabel('Total counts')
        ax3.set_ylabel('Frequency')
    
    # Panel 4: PCA variance
    if 'pca' in adata.uns and 'variance_ratio' in adata.uns['pca']:
        ax4 = fig.add_subplot(gs[1, 0])
        variance_ratio = adata.uns['pca']['variance_ratio'][:20]  # First 20 PCs
        ax4.bar(range(1, len(variance_ratio) + 1), variance_ratio)
        ax4.set_title('PCA Variance Explained')
        ax4.set_xlabel('Principal Component')
        ax4.set_ylabel('Variance Ratio')
    
    # Panel 5: Cluster sizes
    if 'leiden' in adata.obs.columns:
        ax5 = fig.add_subplot(gs[1, 1])
        cluster_counts = adata.obs['leiden'].value_counts().sort_index()
        bars = ax5.bar(range(len(cluster_counts)), cluster_counts.values)
        ax5.set_title('Cluster Sizes')
        ax5.set_xlabel('Cluster')
        ax5.set_ylabel('Number of cells')
        ax5.set_xticks(range(len(cluster_counts)))
        ax5.set_xticklabels(cluster_counts.index)
    
    # Panel 6: Mitochondrial genes
    if 'pct_counts_mt' in adata.obs.columns:
        ax6 = fig.add_subplot(gs[1, 2])
        ax6.hist(adata.obs['pct_counts_mt'], bins=30, alpha=0.7, color='salmon')
        ax6.set_title('Mitochondrial %')
        ax6.set_xlabel('Mitochondrial gene %')
        ax6.set_ylabel('Frequency')
    
    # Panel 7-9: Additional info
    ax7 = fig.add_subplot(gs[2, :])
    ax7.axis('off')
    
    # Add summary statistics
    stats_text = f"""
    Dataset Summary:
    • Total cells: {adata.n_obs:,}
    • Total genes: {adata.n_vars:,}
    """
    
    if 'leiden' in adata.obs.columns:
        n_clusters = len(adata.obs['leiden'].unique())
        stats_text += f"• Clusters identified: {n_clusters}\n"
    
    if 'highly_variable' in adata.var.columns:
        n_hvg = adata.var['highly_variable'].sum()
        stats_text += f"• Highly variable genes: {n_hvg:,}\n"
    
    ax7.text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
    
    plt.suptitle('Single Cell Analysis Summary', fontsize=16, y=0.95)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig 