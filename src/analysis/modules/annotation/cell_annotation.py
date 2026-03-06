"""
Cell annotation module for SingleCellStudio

Provides multiple methods for cell type annotation including:
- Basic marker-based annotation (scanpy only)
- Automated annotation with CellTypist (optional)
- Manual annotation interface
- Reference-based annotation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import logging

from ..base_module import AnalysisModule, ModuleParameter

# Try to import dependencies safely
try:
    from ....dependencies import safe_import
except ImportError:
    # Fallback safe_import function
    def safe_import(package_name: str, module_name: str = None):
        try:
            if module_name:
                full_name = f"{package_name}.{module_name}"
                return __import__(full_name, fromlist=[module_name])
            else:
                return __import__(package_name)
        except ImportError:
            return None

# Safe imports for optional dependencies
celltypist = safe_import('celltypist')
scanpy = safe_import('scanpy')

logger = logging.getLogger("SingleCellStudio.CellAnnotation")

class CellAnnotationModule(AnalysisModule):
    """
    Cell type annotation module with multiple methods
    """
    
    @property
    def name(self) -> str:
        return "Cell Annotation"
    
    @property
    def description(self) -> str:
        return "Annotate cell types using various methods including automated tools and marker genes"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def required_dependencies(self) -> List[str]:
        return ['scanpy', 'pandas', 'numpy']
    
    @property
    def optional_dependencies(self) -> List[str]:
        return ['celltypist']
    
    @property
    def required_data_keys(self) -> List[str]:
        return ['leiden']  # Requires clustering results
    
    def get_parameters(self) -> List[ModuleParameter]:
        """Get configurable parameters for cell annotation"""
        return [
            ModuleParameter(
                name='method',
                display_name='Annotation Method',
                param_type=str,
                default_value='auto',
                description='Method to use for cell annotation',
                options=['auto', 'marker_based', 'reference_based', 'celltypist']
            ),
            ModuleParameter(
                name='confidence_threshold',
                display_name='Confidence Threshold',
                param_type=float,
                default_value=0.5,
                description='Minimum confidence score for automated annotations',
                min_value=0.0,
                max_value=1.0
            ),
            ModuleParameter(
                name='custom_markers',
                display_name='Custom Marker Genes',
                param_type=str,
                default_value='',
                description='Custom marker genes in JSON format: {"T cells": ["CD3D", "CD3E"], "B cells": ["CD19", "MS4A1"]}'
            )
        ]
    
    def validate_data(self, adata) -> Tuple[bool, str]:
        """Validate input data for cell annotation"""
        try:
            # Check if data exists
            if adata is None:
                return False, "No data provided"
            
            # Check if clustering results exist
            if 'leiden' not in adata.obs.columns:
                return False, "Clustering results (leiden) not found. Please run clustering first."
            
            # Check if we have gene expression data
            if adata.X is None or adata.X.shape[0] == 0:
                return False, "No gene expression data found"
            
            # Check if we have gene names
            if adata.var.index is None or len(adata.var.index) == 0:
                return False, "No gene names found in data"
            
            return True, "Data validation successful"
            
        except Exception as e:
            return False, f"Data validation error: {str(e)}"
    
    def run_analysis(self, adata, method: str = 'auto', **kwargs) -> Dict[str, Any]:
        """
        Run cell annotation analysis
        
        Args:
            adata: AnnData object with clustered single-cell data
            method: Annotation method ('auto', 'basic', 'celltypist', 'marker_based')
            **kwargs: Additional parameters
        """
        # Validate data first
        is_valid, error_msg = self.validate_data(adata)
        if not is_valid:
            return {'error': error_msg, 'success': False}
        
        # Determine method to use
        if method == 'auto':
            method = 'celltypist' if celltypist is not None else 'reference_based'
        
        results = {
            'method_used': method,
            'success': False,
            'cell_types': [],
            'confidence': [],
            'summary': {}
        }
        
        try:
            # Run the selected annotation method
            if method == 'celltypist' and celltypist is not None:
                annotation_results = self._run_celltypist_annotation(adata, **kwargs)
            elif method == 'marker_based':
                annotation_results = self._run_marker_based_annotation(adata, **kwargs)
            elif method == 'reference_based':
                annotation_results = self._run_reference_based_annotation(adata, **kwargs)
            else:
                # Default to marker-based annotation
                annotation_results = self._run_marker_based_annotation(adata, **kwargs)
                results['method_used'] = 'marker_based'
            
            # Merge results
            results.update(annotation_results)
            results['success'] = True
            
            # Add annotations to adata
            if 'cell_types' in annotation_results:
                adata.obs['cell_type'] = annotation_results['cell_types']
                adata.obs['cell_type'] = adata.obs['cell_type'].astype('category')
            
            if 'confidence' in annotation_results:
                adata.obs['annotation_confidence'] = annotation_results['confidence']
            
            # Generate summary
            results['summary'] = self._generate_summary(results)
            
        except Exception as e:
            logger.error(f"Cell annotation failed: {e}")
            results['error'] = str(e)
            results['success'] = False
        
        return results
    
    def _run_reference_based_annotation(self, adata, **kwargs) -> Dict[str, Any]:
        """Run reference-based annotation using cell type signatures"""
        try:
            # Comprehensive cell type gene signatures
            cell_type_signatures = {
                'T cells': {
                    'positive': ['CD3D', 'CD3E', 'CD3G', 'CD2', 'TRAC', 'TRBC1', 'TRBC2'],
                    'negative': ['CD19', 'MS4A1', 'CD14', 'LYZ']
                },
                'CD4+ T cells': {
                    'positive': ['CD3D', 'CD4', 'IL7R', 'CCR7', 'SELL', 'TCF7'],
                    'negative': ['CD8A', 'CD8B', 'GNLY', 'NKG7']
                },
                'CD8+ T cells': {
                    'positive': ['CD3D', 'CD8A', 'CD8B', 'GZMK', 'CCL5'],
                    'negative': ['CD4', 'IL7R', 'GNLY', 'NKG7']
                },
                'Regulatory T cells': {
                    'positive': ['CD3D', 'CD4', 'FOXP3', 'IL2RA', 'CTLA4'],
                    'negative': ['CD8A', 'GNLY', 'NKG7']
                },
                'B cells': {
                    'positive': ['CD19', 'MS4A1', 'CD79A', 'CD79B', 'BANK1', 'BLK'],
                    'negative': ['CD3D', 'CD14', 'LYZ']
                },
                'Plasma cells': {
                    'positive': ['IGHG1', 'IGHG2', 'IGHG3', 'MZB1', 'SDC1', 'CD38', 'XBP1'],
                    'negative': ['CD19', 'MS4A1', 'CD3D']
                },
                'NK cells': {
                    'positive': ['GNLY', 'NKG7', 'KLRD1', 'NCAM1', 'KLRF1', 'KLRB1'],
                    'negative': ['CD3D', 'CD19', 'CD14']
                },
                'Monocytes': {
                    'positive': ['CD14', 'LYZ', 'S100A9', 'S100A8', 'VCAN', 'MNDA'],
                    'negative': ['CD3D', 'CD19', 'GNLY']
                },
                'Macrophages': {
                    'positive': ['CD68', 'CD163', 'MSR1', 'MRC1', 'MARCO', 'C1QA'],
                    'negative': ['CD3D', 'CD19', 'CD14']
                },
                'Dendritic cells': {
                    'positive': ['FCER1A', 'CST3', 'CLEC9A', 'CLEC10A', 'CD1C'],
                    'negative': ['CD3D', 'CD19', 'CD14', 'LYZ']
                },
                'Neutrophils': {
                    'positive': ['FCGR3B', 'CEACAM8', 'CSF3R', 'S100A12'],
                    'negative': ['CD3D', 'CD19', 'CD14']
                },
                'Endothelial cells': {
                    'positive': ['PECAM1', 'VWF', 'CDH5', 'KDR', 'FLT1'],
                    'negative': ['CD3D', 'CD19', 'CD14', 'LYZ']
                },
                'Fibroblasts': {
                    'positive': ['COL1A1', 'COL1A2', 'DCN', 'LUM', 'PDGFRA'],
                    'negative': ['CD3D', 'CD19', 'CD14', 'PECAM1']
                },
                'Epithelial cells': {
                    'positive': ['EPCAM', 'KRT8', 'KRT18', 'KRT19', 'CDH1'],
                    'negative': ['CD3D', 'CD19', 'CD14', 'VIM']
                }
            }
            
            # Calculate signature scores for each cluster
            unique_clusters = sorted(adata.obs['leiden'].unique())
            cluster_annotations = {}
            cluster_scores = {}
            
            for cluster in unique_clusters:
                cluster_mask = adata.obs['leiden'] == cluster
                cluster_data = adata[cluster_mask, :]
                
                best_cell_type = 'Unknown'
                best_score = -1
                cell_type_scores = {}
                
                for cell_type, signature in cell_type_signatures.items():
                    # Calculate positive signature score
                    pos_genes = [g for g in signature['positive'] if g in adata.var.index]
                    neg_genes = [g for g in signature['negative'] if g in adata.var.index]
                    
                    pos_score = 0
                    neg_score = 0
                    
                    if pos_genes:
                        pos_data = cluster_data[:, pos_genes]
                        if hasattr(pos_data.X, 'toarray'):
                            pos_expr = pos_data.X.toarray()
                        else:
                            pos_expr = pos_data.X
                        pos_score = np.mean(pos_expr)
                    
                    if neg_genes:
                        neg_data = cluster_data[:, neg_genes]
                        if hasattr(neg_data.X, 'toarray'):
                            neg_expr = neg_data.X.toarray()
                        else:
                            neg_expr = neg_data.X
                        neg_score = np.mean(neg_expr)
                    
                    # Combined score: positive markers - negative markers
                    signature_score = pos_score - (neg_score * 0.5)  # Weight negative markers less
                    cell_type_scores[cell_type] = signature_score
                    
                    if signature_score > best_score:
                        best_score = signature_score
                        best_cell_type = cell_type
                
                cluster_annotations[cluster] = best_cell_type
                cluster_scores[cluster] = cell_type_scores
            
            # Map annotations to all cells
            cell_types = adata.obs['leiden'].map(cluster_annotations).values
            
            # Calculate confidence scores based on signature strength
            confidence_scores = []
            for i, cell in enumerate(adata.obs.index):
                cluster = adata.obs.loc[cell, 'leiden']
                scores = cluster_scores.get(cluster, {})
                if scores:
                    best_score = max(scores.values())
                    second_best = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
                    # Confidence based on margin between best and second-best
                    margin = best_score - second_best
                    confidence = min(max(margin / 3.0, 0.1), 1.0)  # Normalize to 0.1-1.0
                else:
                    confidence = 0.1
                confidence_scores.append(confidence)
            
            return {
                'cell_types': cell_types,
                'confidence': np.array(confidence_scores),
                'method_details': {
                    'signatures_used': cell_type_signatures,
                    'cluster_annotations': cluster_annotations,
                    'cluster_scores': cluster_scores,
                    'available_genes': {ct: {
                        'positive': [g for g in sig['positive'] if g in adata.var.index],
                        'negative': [g for g in sig['negative'] if g in adata.var.index]
                    } for ct, sig in cell_type_signatures.items()}
                }
            }
            
        except Exception as e:
            logger.warning(f"Reference-based annotation failed: {e}")
            return self._run_marker_based_annotation(adata, **kwargs)
    
    def _run_celltypist_annotation(self, adata, **kwargs) -> Dict[str, Any]:
        """Run CellTypist automated annotation"""
        try:
            if celltypist is None:
                logger.warning("CellTypist not available, falling back to reference-based annotation")
                return self._run_reference_based_annotation(adata, **kwargs)
            
            # CellTypist requires raw counts and specific format
            logger.info("Running CellTypist annotation...")
            
            # CellTypist expects raw counts, but we'll work with what we have
            # This is a basic implementation - full CellTypist integration would need:
            # 1. Raw count data
            # 2. Proper preprocessing
            # 3. Model selection
            
            # For now, provide informative message and fall back
            logger.info("CellTypist requires specific data preprocessing. Using reference-based method instead.")
            return self._run_reference_based_annotation(adata, **kwargs)
            
        except Exception as e:
            logger.warning(f"CellTypist annotation failed: {e}")
            return self._run_reference_based_annotation(adata, **kwargs)
    
    def _run_marker_based_annotation(self, adata, **kwargs) -> Dict[str, Any]:
        """Run marker gene-based annotation"""
        try:
            # Default marker genes for common cell types
            default_markers = {
                'T cells': ['CD3D', 'CD3E', 'CD3G', 'CD2'],
                'CD4+ T cells': ['CD3D', 'CD4', 'IL7R'],
                'CD8+ T cells': ['CD3D', 'CD8A', 'CD8B'],
                'B cells': ['CD19', 'MS4A1', 'CD79A', 'CD79B'],
                'NK cells': ['GNLY', 'NKG7', 'KLRD1', 'NCAM1'],
                'Monocytes': ['CD14', 'LYZ', 'S100A9', 'FCGR3A'],
                'Dendritic cells': ['FCER1A', 'CST3', 'CLEC9A'],
                'Plasma cells': ['IGHG1', 'MZB1', 'SDC1', 'CD38'],
                'Macrophages': ['CD68', 'CD163', 'MSR1'],
                'Neutrophils': ['FCGR3B', 'CEACAM8', 'CSF3R']
            }
            
            # Check for custom markers
            custom_markers_str = kwargs.get('custom_markers', '')
            marker_genes = default_markers.copy()
            
            if custom_markers_str.strip():
                try:
                    import json
                    custom_markers = json.loads(custom_markers_str)
                    if isinstance(custom_markers, dict):
                        marker_genes.update(custom_markers)
                        logger.info(f"Using custom marker genes: {list(custom_markers.keys())}")
                except Exception as e:
                    logger.warning(f"Failed to parse custom markers: {e}, using defaults")
            
            # Calculate marker expression scores for each cluster
            unique_clusters = sorted(adata.obs['leiden'].unique())
            cluster_annotations = {}
            cluster_scores = {}
            
            for cluster in unique_clusters:
                cluster_mask = adata.obs['leiden'] == cluster
                cluster_data = adata[cluster_mask, :]
                
                best_cell_type = 'Unknown'
                best_score = 0
                cell_type_scores = {}
                
                for cell_type, markers in marker_genes.items():
                    # Find markers that exist in the data
                    available_markers = [m for m in markers if m in adata.var.index]
                    
                    if available_markers:
                        # Calculate mean expression of marker genes in this cluster
                        marker_data = cluster_data[:, available_markers]
                        if hasattr(marker_data.X, 'toarray'):
                            marker_expr = marker_data.X.toarray()
                        else:
                            marker_expr = marker_data.X
                        
                        mean_expr = np.mean(marker_expr)
                        cell_type_scores[cell_type] = mean_expr
                        
                        if mean_expr > best_score:
                            best_score = mean_expr
                            best_cell_type = cell_type
                
                cluster_annotations[cluster] = best_cell_type
                cluster_scores[cluster] = cell_type_scores
            
            # Map annotations to all cells
            cell_types = adata.obs['leiden'].map(cluster_annotations).values
            
            # Calculate confidence scores based on marker expression strength
            confidence_scores = []
            for i, cell in enumerate(adata.obs.index):
                cluster = adata.obs.loc[cell, 'leiden']
                scores = cluster_scores.get(cluster, {})
                if scores:
                    max_score = max(scores.values())
                    # Normalize confidence (assuming max expression around 5-10)
                    confidence = min(max_score / 5.0, 1.0)
                else:
                    confidence = 0.3
                confidence_scores.append(confidence)
            
            return {
                'cell_types': cell_types,
                'confidence': np.array(confidence_scores),
                'method_details': {
                    'marker_genes_used': marker_genes,
                    'cluster_annotations': cluster_annotations,
                    'cluster_scores': cluster_scores,
                    'available_markers': {ct: [m for m in markers if m in adata.var.index] 
                                        for ct, markers in marker_genes.items()}
                }
            }
            
        except Exception as e:
            logger.warning(f"Marker-based annotation failed: {e}")
            return self._run_basic_annotation(adata, **kwargs)
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for annotation results"""
        try:
            if 'cell_types' not in results:
                return {'error': 'No cell type annotations found'}
            
            cell_types = results['cell_types']
            confidence_scores = results.get('confidence', np.zeros(len(cell_types)))
            
            # Count cell types
            unique_types, counts = np.unique(cell_types, return_counts=True)
            cell_type_counts = dict(zip(unique_types, counts))
            
            # Calculate confidence statistics
            mean_confidence = np.mean(confidence_scores)
            high_confidence_count = np.sum(confidence_scores > 0.7)
            
            return {
                'total_cells': len(cell_types),
                'unique_cell_types': len(unique_types),
                'cell_type_counts': cell_type_counts,
                'mean_confidence': mean_confidence,
                'high_confidence_cells': high_confidence_count,
                'method_used': results['method_used']
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {'error': str(e)}
    
    def get_available_methods(self) -> List[str]:
        """Get available annotation methods"""
        methods = ['auto', 'marker_based', 'reference_based']
        
        # Check if celltypist is available
        try:
            import celltypist
            methods.append('celltypist')
        except ImportError:
            pass
            
        return methods
    
    def get_visualization_options(self) -> List[str]:
        """Get available visualization types for annotation results"""
        return ['umap_celltype', 'celltype_proportions', 'summary']
    
    def create_visualization(self, adata, results: Dict[str, Any], 
                           plot_type: str = 'summary', **kwargs) -> Any:
        """Create visualization for annotation results"""
        try:
            import matplotlib.pyplot as plt
            
            if plot_type == 'umap_celltype':
                return self._plot_umap_celltypes(adata, results, **kwargs)
            elif plot_type == 'celltype_proportions':
                return self._plot_celltype_proportions(results, **kwargs)
            else:
                return self._plot_summary(adata, results, **kwargs)
                
        except Exception as e:
            logger.error(f"Visualization error: {e}")
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.text(0.5, 0.5, f"Visualization error:\n{str(e)}", 
                   ha='center', va='center', transform=ax.transAxes)
            return fig
    
    def _plot_umap_celltypes(self, adata, results, **kwargs):
        """Plot UMAP colored by cell types"""
        import matplotlib.pyplot as plt
        
        if 'X_umap' not in adata.obsm:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.text(0.5, 0.5, "UMAP coordinates not found.\nPlease run UMAP first.", 
                   ha='center', va='center', transform=ax.transAxes)
            return fig
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        umap_coords = adata.obsm['X_umap']
        cell_types = results.get('cell_types', adata.obs.get('cell_type', 'Unknown'))
        
        unique_types = np.unique(cell_types)
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_types)))
        
        for i, cell_type in enumerate(unique_types):
            mask = cell_types == cell_type
            ax.scatter(umap_coords[mask, 0], umap_coords[mask, 1], 
                      c=[colors[i]], label=cell_type, alpha=0.7, s=10)
        
        ax.set_xlabel('UMAP 1')
        ax.set_ylabel('UMAP 2')
        ax.set_title(f'Cell Type Annotation ({results.get("method_used", "Unknown")} method)')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        return fig
    
    def _plot_celltype_proportions(self, results, **kwargs):
        """Plot cell type proportions as pie chart"""
        import matplotlib.pyplot as plt
        
        summary = results.get('summary', {})
        cell_type_counts = summary.get('cell_type_counts', {})
        
        if not cell_type_counts:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.text(0.5, 0.5, "No cell type data available", 
                   ha='center', va='center', transform=ax.transAxes)
            return fig
        
        fig, ax = plt.subplots(figsize=(8, 8))
        
        labels = list(cell_type_counts.keys())
        sizes = list(cell_type_counts.values())
        
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title('Cell Type Proportions')
        
        plt.tight_layout()
        return fig
    
    def _plot_summary(self, adata, results, **kwargs):
        """Create summary plot with multiple panels"""
        import matplotlib.pyplot as plt
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Panel 1: UMAP with cell types
        if 'X_umap' in adata.obsm and 'cell_types' in results:
            umap_coords = adata.obsm['X_umap']
            cell_types = results['cell_types']
            unique_types = np.unique(cell_types)
            colors = plt.cm.tab10(np.linspace(0, 1, min(len(unique_types), 10)))
            
            for i, cell_type in enumerate(unique_types[:10]):
                mask = cell_types == cell_type
                ax1.scatter(umap_coords[mask, 0], umap_coords[mask, 1], 
                           c=[colors[i]], label=cell_type, alpha=0.6, s=5)
            
            ax1.set_title('UMAP - Cell Types')
            ax1.legend(fontsize=8)
        else:
            ax1.text(0.5, 0.5, "UMAP not available", ha='center', va='center')
        
        # Panel 2: Confidence distribution
        confidence_scores = results.get('confidence', [])
        if len(confidence_scores) > 0:
            ax2.hist(confidence_scores, bins=20, alpha=0.7, edgecolor='black')
            ax2.set_title('Confidence Distribution')
            ax2.set_xlabel('Confidence Score')
            ax2.set_ylabel('Count')
        else:
            ax2.text(0.5, 0.5, "No confidence data", ha='center', va='center')
        
        # Panel 3: Cell type counts
        summary = results.get('summary', {})
        cell_type_counts = summary.get('cell_type_counts', {})
        if cell_type_counts:
            types = list(cell_type_counts.keys())[:10]
            counts = [cell_type_counts[t] for t in types]
            ax3.bar(range(len(types)), counts)
            ax3.set_title('Cell Type Counts')
            ax3.set_xlabel('Cell Type')
            ax3.set_ylabel('Count')
            ax3.set_xticks(range(len(types)))
            ax3.set_xticklabels(types, rotation=45, ha='right')
        else:
            ax3.text(0.5, 0.5, "No count data", ha='center', va='center')
        
        # Panel 4: Summary statistics
        ax4.axis('off')
        if summary:
            stats_text = f"""Annotation Summary
Method: {results.get('method_used', 'Unknown')}
Total cells: {summary.get('total_cells', 'N/A')}
Unique cell types: {summary.get('unique_cell_types', 'N/A')}
Mean confidence: {summary.get('mean_confidence', 0):.2f}
High confidence: {summary.get('high_confidence_cells', 'N/A')}"""
            ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, 
                    fontsize=10, verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        return fig 