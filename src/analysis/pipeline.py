"""
Analysis Pipeline Module for Single Cell Analysis

This module provides comprehensive analysis pipelines that orchestrate
the entire single cell analysis workflow from QC to clustering.
"""

import numpy as np
import pandas as pd
import scanpy as sc
from typing import Dict, List, Optional, Tuple, Union, Any
import logging
import time
from datetime import datetime
import os
from pathlib import Path
import anndata as ad
import json

from . import quality_control
from . import normalization
from . import dimensionality_reduction
from . import clustering

from .quality_control import QualityControl
from .normalization import Normalizer
from .dimensionality_reduction import DimensionalityReducer
from .clustering import ClusterAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisPipeline:
    """
    Base class for single cell analysis pipelines
    
    This class provides the framework for creating and executing
    comprehensive single cell analysis workflows.
    """
    
    def __init__(self, adata=None, name="Analysis Pipeline", output_dir=None):
        """
        Initialize AnalysisPipeline
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        name : str
            Name of the pipeline
        output_dir : str, optional
            Directory to save intermediate results and outputs
        """
        self.adata = adata
        self.name = name
        self.steps = []
        self.results = {}
        self.execution_log = []
        self.start_time = None
        self.end_time = None
        
        # Set up output directory
        self.output_dir = self._setup_output_directory(output_dir)
        
        # Initialize analysis modules
        self.qc = QualityControl(adata)
        self.normalizer = Normalizer(adata)
        self.reducer = DimensionalityReducer(adata)
        self.clusterer = ClusterAnalyzer(adata)
        
    def _setup_output_directory(self, output_dir=None):
        """
        Set up output directory for saving results
        
        Parameters:
        -----------
        output_dir : str, optional
            Custom output directory path
            
        Returns:
        --------
        Path : Output directory path
        """
        if output_dir is None:
            # Create default output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(f"results/analysis_results_{timestamp}")
        else:
            output_dir = Path(output_dir)
            
        # Create directory structure
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "intermediate_data").mkdir(exist_ok=True)
        (output_dir / "plots").mkdir(exist_ok=True)
        (output_dir / "metadata").mkdir(exist_ok=True)
        (output_dir / "logs").mkdir(exist_ok=True)
        
        logger.info(f"Output directory set up: {output_dir.absolute()}")
        return output_dir
        
    def _save_intermediate_data(self, step_name, adata_copy=None):
        """
        Save intermediate data after key analysis steps only
        
        Parameters:
        -----------
        step_name : str
            Name of the analysis step
        adata_copy : anndata.AnnData, optional
            Copy of data to save (if None, uses self.adata)
        """
        # Only save data for key steps
        key_steps = ['normalize_data', 'clustering']
        
        if step_name not in key_steps:
            # Still save step-specific metadata for all steps
            if adata_copy is None:
                adata_copy = self.adata
            self._save_step_metadata(step_name, adata_copy)
            return
        
        try:
            if adata_copy is None:
                adata_copy = self.adata.copy()
                
            # Save AnnData object for key steps only
            output_file = self.output_dir / "intermediate_data" / f"{step_name}.h5ad"
            adata_copy.write(output_file)
            logger.info(f"Saved key checkpoint: {output_file}")
            
            # Save step-specific metadata
            self._save_step_metadata(step_name, adata_copy)
            
        except Exception as e:
            logger.warning(f"Failed to save intermediate data for {step_name}: {e}")
            
    def _save_step_metadata(self, step_name, adata):
        """
        Save metadata specific to each analysis step
        
        Parameters:
        -----------
        step_name : str
            Name of the analysis step
        adata : anndata.AnnData
            Annotated data object
        """
        metadata_dir = self.output_dir / "metadata"
        
        try:
            if step_name == "calculate_qc_metrics":
                # Save QC metrics
                qc_metrics = adata.obs[['n_genes_by_counts', 'total_counts', 'pct_counts_mt']].copy()
                qc_metrics.to_csv(metadata_dir / "qc_metrics.csv")
                
            elif step_name == "filter_cells":
                # Save cell filtering stats
                filter_stats = {
                    'n_cells_before': len(adata.obs),
                    'n_cells_after': len(adata.obs),
                    'cells_removed': 0  # Will be updated in actual filtering
                }
                pd.Series(filter_stats).to_csv(metadata_dir / "cell_filtering_stats.csv")
                
            elif step_name == "filter_genes":
                # Save gene filtering stats
                gene_stats = {
                    'n_genes_before': adata.n_vars,
                    'n_genes_after': adata.n_vars,
                    'genes_removed': 0
                }
                pd.Series(gene_stats).to_csv(metadata_dir / "gene_filtering_stats.csv")
                
            elif step_name == "find_variable_genes":
                # Save highly variable genes
                if 'highly_variable' in adata.var:
                    hvg_genes = adata.var[adata.var['highly_variable']].copy()
                    hvg_genes.to_csv(metadata_dir / "highly_variable_genes.csv")
                    
            elif step_name == "run_pca":
                # Save PCA results
                if 'X_pca' in adata.obsm:
                    pca_coords = pd.DataFrame(
                        adata.obsm['X_pca'],
                        index=adata.obs.index,
                        columns=[f'PC{i+1}' for i in range(adata.obsm['X_pca'].shape[1])]
                    )
                    pca_coords.to_csv(metadata_dir / "pca_coordinates.csv")
                    
                    # Save PCA variance explained
                    if 'pca' in adata.uns:
                        variance_ratio = pd.Series(
                            adata.uns['pca']['variance_ratio'],
                            index=[f'PC{i+1}' for i in range(len(adata.uns['pca']['variance_ratio']))]
                        )
                        variance_ratio.to_csv(metadata_dir / "pca_variance_explained.csv")
                        
            elif step_name == "run_umap":
                # Save UMAP coordinates
                if 'X_umap' in adata.obsm:
                    umap_coords = pd.DataFrame(
                        adata.obsm['X_umap'],
                        index=adata.obs.index,
                        columns=['UMAP1', 'UMAP2']
                    )
                    umap_coords.to_csv(metadata_dir / "umap_coordinates.csv")
                    
            elif step_name == "clustering":
                # Save clustering results
                if 'leiden' in adata.obs:
                    cluster_results = adata.obs[['leiden']].copy()
                    cluster_results.to_csv(metadata_dir / "clustering_results.csv")
                    
                    # Save cluster statistics
                    cluster_stats = adata.obs['leiden'].value_counts().sort_index()
                    cluster_stats.to_csv(metadata_dir / "cluster_statistics.csv")
                    
        except Exception as e:
            logger.warning(f"Failed to save metadata for {step_name}: {e}")
            
    def _save_final_metadata(self):
        """Save complete metadata after pipeline completion"""
        try:
            metadata_dir = self.output_dir / "metadata"
            
            # Save complete cell metadata
            cell_metadata = self.adata.obs.copy()
            cell_metadata.to_csv(metadata_dir / "final_cell_metadata.csv")
            
            # Save complete gene metadata
            gene_metadata = self.adata.var.copy()
            gene_metadata.to_csv(metadata_dir / "final_gene_metadata.csv")
            
            # Save analysis summary
            summary = self.get_summary()
            summary_df = pd.Series(summary).to_frame('value')
            summary_df.to_csv(metadata_dir / "analysis_summary.csv")
            
            # Save pipeline parameters (if available)
            if hasattr(self, 'params'):
                params_df = pd.Series(self.params).to_frame('value')
                params_df.to_csv(metadata_dir / "pipeline_parameters.csv")
                
            logger.info(f"Final metadata saved to: {metadata_dir}")
            
        except Exception as e:
            logger.warning(f"Failed to save final metadata: {e}")
            
    def _save_execution_log(self):
        """Save pipeline execution log"""
        try:
            log_file = self.output_dir / "logs" / "execution_log.csv"
            log_df = pd.DataFrame(self.execution_log)
            log_df.to_csv(log_file, index=False)
            logger.info(f"Execution log saved: {log_file}")
        except Exception as e:
            logger.warning(f"Failed to save execution log: {e}")
        
    def add_step(self, step_name, function, **kwargs):
        """
        Add a step to the pipeline
        
        Parameters:
        -----------
        step_name : str
            Name of the analysis step
        function : callable
            Function to execute
        **kwargs : dict
            Arguments for the function
        """
        self.steps.append({
            'name': step_name,
            'function': function,
            'kwargs': kwargs,
            'completed': False,
            'duration': None,
            'error': None
        })
        
    def execute_step(self, step_index):
        """
        Execute a single pipeline step
        
        Parameters:
        -----------
        step_index : int
            Index of the step to execute
            
        Returns:
        --------
        bool : Success status
        """
        if step_index >= len(self.steps):
            logger.error(f"Step index {step_index} out of range")
            return False
            
        step = self.steps[step_index]
        step_name = step['name']
        
        logger.info(f"Executing step {step_index + 1}/{len(self.steps)}: {step_name}")
        
        start_time = time.time()
        
        try:
            # Execute the step function
            result = step['function'](**step['kwargs'])
            
            # Save intermediate data after successful step
            self._save_intermediate_data(step_name)
            
            # Record results
            step['completed'] = True
            step['duration'] = time.time() - start_time
            self.results[step_name] = result
            
            # Log execution
            self.execution_log.append({
                'step': step_name,
                'timestamp': datetime.now(),
                'duration': step['duration'],
                'status': 'success'
            })
            
            logger.info(f"Step '{step_name}' completed in {step['duration']:.2f}s")
            return True
            
        except Exception as e:
            step['error'] = str(e)
            step['duration'] = time.time() - start_time
            
            # Log error
            self.execution_log.append({
                'step': step_name,
                'timestamp': datetime.now(),
                'duration': step['duration'],
                'status': 'error',
                'error': str(e)
            })
            
            logger.error(f"Step '{step_name}' failed: {e}")
            return False
            
    def execute_pipeline(self, continue_on_error=False):
        """
        Execute the entire pipeline
        
        Parameters:
        -----------
        continue_on_error : bool
            Whether to continue execution if a step fails
            
        Returns:
        --------
        dict : Pipeline execution results
        """
        if not self.steps:
            logger.warning("No steps defined in pipeline")
            return self.get_summary()
            
        logger.info(f"Starting pipeline execution: {self.name}")
        logger.info(f"Output directory: {self.output_dir}")
        self.start_time = datetime.now()
        
        success_count = 0
        
        for i, step in enumerate(self.steps):
            success = self.execute_step(i)
            
            if success:
                success_count += 1
            elif not continue_on_error:
                logger.error(f"Pipeline stopped at step {i + 1} due to error")
                break
                
        self.end_time = datetime.now()
        total_duration = (self.end_time - self.start_time).total_seconds()
        
        # Save final metadata and logs
        self._save_final_metadata()
        self._save_execution_log()
        
        logger.info(f"Pipeline completed: {success_count}/{len(self.steps)} steps successful "
                   f"in {total_duration:.2f}s")
        logger.info(f"Results saved to: {self.output_dir}")
        
        return self.get_summary()
        
    def get_summary(self):
        """Get pipeline execution summary"""
        completed_steps = sum(1 for step in self.steps if step['completed'])
        total_duration = sum(step['duration'] or 0 for step in self.steps)
        
        summary = {
            'pipeline_name': self.name,
            'total_steps': len(self.steps),
            'completed_steps': completed_steps,
            'success_rate': completed_steps / len(self.steps) if self.steps else 0,
            'total_duration': total_duration,
            'execution_time': total_duration,  # Add for GUI compatibility
            'start_time': self.start_time,
            'end_time': self.end_time,
            'output_directory': str(self.output_dir),
            'steps': self.steps,
            'step_results': self.results,  # Add for GUI compatibility
            'execution_log': self.execution_log,
            'results': self.results
        }
        
        return summary


class StandardPipeline(AnalysisPipeline):
    """
    Standard single cell analysis pipeline
    
    This pipeline implements a typical single cell RNA-seq analysis workflow:
    1. Quality control and filtering
    2. Normalization
    3. Feature selection
    4. Dimensionality reduction (PCA)
    5. Neighborhood graph construction
    6. UMAP embedding
    7. Clustering
    """
    
    def __init__(self, adata=None, output_dir=None, **params):
        """
        Initialize StandardPipeline
        
        Parameters:
        -----------
        adata : anndata.AnnData, optional
            Annotated data object
        output_dir : str, optional
            Directory to save intermediate results and outputs
        **params : dict
            Pipeline parameters
        """
        super().__init__(adata, "Standard Single Cell Analysis Pipeline", output_dir)
        
        # Default parameters
        self.params = {
            # QC parameters
            'min_genes': 200,
            'max_genes': None,
            'max_pct_mt': 20,
            'min_cells': 3,
            
            # Normalization parameters
            'target_sum': 1e4,
            'n_top_genes': 2000,
            
            # PCA parameters
            'n_pcs': 40,
            
            # Neighborhood parameters
            'n_neighbors': 10,
            
            # UMAP parameters
            'min_dist': 0.5,
            
            # Clustering parameters
            'resolution': 0.5,
            'clustering_method': 'leiden',
            
            # General parameters
            'random_state': 42
        }
        
        # Update with provided parameters
        self.params.update(params)
        
        # Build pipeline
        self._build_pipeline()
        
    def _build_pipeline(self):
        """Build the standard analysis pipeline"""
        
        # Step 1: Calculate QC metrics
        self.add_step(
            "calculate_qc_metrics",
            self.qc.calculate_qc_metrics,
            adata=self.adata
        )
        
        # Step 2: Filter cells
        self.add_step(
            "filter_cells",
            self.qc.filter_cells,
            adata=self.adata,
            min_genes=self.params['min_genes'],
            max_genes=self.params['max_genes'],
            max_pct_mt=self.params['max_pct_mt']
        )
        
        # Step 3: Filter genes
        self.add_step(
            "filter_genes",
            self.qc.filter_genes,
            adata=self.adata,
            min_cells=self.params['min_cells']
        )
        
        # Step 4: Normalize data
        self.add_step(
            "normalize_data",
            self.normalizer.log_normalize,
            adata=self.adata,
            target_sum=self.params['target_sum']
        )
        
        # Step 5: Find highly variable genes
        self.add_step(
            "find_variable_genes",
            self._find_variable_genes,
            n_top_genes=self.params['n_top_genes']
        )
        
        # Step 6: Scale data
        self.add_step(
            "scale_data",
            self.normalizer.scale_data,
            adata=self.adata,
            max_value=10
        )
        
        # Step 7: Principal component analysis
        self.add_step(
            "run_pca",
            self.reducer.run_pca,
            adata=self.adata,
            n_comps=self.params['n_pcs'],
            random_state=self.params['random_state']
        )
        
        # Step 8: Compute neighborhood graph
        self.add_step(
            "compute_neighbors",
            self._compute_neighbors,
            n_neighbors=self.params['n_neighbors']
        )
        
        # Step 9: UMAP embedding
        self.add_step(
            "run_umap",
            self.reducer.run_umap,
            adata=self.adata,
            min_dist=self.params['min_dist'],
            random_state=self.params['random_state']
        )
        
        # Step 10: Clustering
        if self.params['clustering_method'] == 'leiden':
            self.add_step(
                "clustering",
                self.clusterer.leiden_clustering,
                adata=self.adata,
                resolution=self.params['resolution'],
                random_state=self.params['random_state']
            )
        else:
            self.add_step(
                "clustering",
                self.clusterer.louvain_clustering,
                adata=self.adata,
                resolution=self.params['resolution'],
                random_state=self.params['random_state']
            )
            
    def _find_variable_genes(self, n_top_genes=2000):
        """Find highly variable genes"""
        logger.info(f"Finding {n_top_genes} highly variable genes")
        sc.pp.highly_variable_genes(self.adata, n_top_genes=n_top_genes)
        n_variable = self.adata.var['highly_variable'].sum()
        logger.info(f"Found {n_variable} highly variable genes")
        return {'n_variable_genes': n_variable}
        
    def _compute_neighbors(self, n_neighbors=10):
        """Compute neighborhood graph"""
        logger.info(f"Computing neighborhood graph with {n_neighbors} neighbors")
        sc.pp.neighbors(self.adata, n_neighbors=n_neighbors, 
                       random_state=self.params['random_state'])
        return {'n_neighbors': n_neighbors}
        
    def get_analysis_summary(self):
        """Get comprehensive analysis summary"""
        summary = self.get_summary()
        
        # Add data statistics
        if self.adata is not None:
            summary['data_info'] = {
                'n_cells': self.adata.n_obs,
                'n_genes': self.adata.n_vars,
                'n_variable_genes': self.adata.var['highly_variable'].sum() if 'highly_variable' in self.adata.var else 0,
                'n_clusters': len(self.adata.obs['leiden'].unique()) if 'leiden' in self.adata.obs else 0
            }
            
        # Add QC summary
        if hasattr(self.qc, 'qc_metrics'):
            summary['qc_metrics'] = self.qc.qc_metrics
            
        # Add filter summary
        if hasattr(self.qc, 'filter_stats'):
            summary['filter_stats'] = self.qc.filter_stats
            
        return summary


def find_variable_genes(adata, n_top_genes=2000):
    """Find highly variable genes"""
    logger.info(f"Finding {n_top_genes} highly variable genes")
    sc.pp.highly_variable_genes(adata, n_top_genes=n_top_genes)
    n_variable = adata.var['highly_variable'].sum()
    logger.info(f"Found {n_variable} highly variable genes")
    return adata


def run_standard_pipeline(adata, output_dir=None, min_genes=200, min_cells=3, 
                            target_sum=10000, n_top_genes=2000, n_pcs=40, 
                            resolution=0.5, save_checkpoints=True,
                            progress_callback=None):
    """
    Run a standard single-cell analysis pipeline from QC to clustering.
    
    Args:
        adata (ad.AnnData): The annotated data matrix.
        output_dir (str or Path): Directory to save results and logs.
        min_genes (int): Minimum number of genes expressed in a cell to keep.
        min_cells (int): Minimum number of cells expressing a gene to keep.
        target_sum (int): Target total counts for normalization.
        n_top_genes (int): Number of highly variable genes to select.
        n_pcs (int): Number of principal components to compute.
        resolution (float): Resolution for Leiden clustering.
        save_checkpoints (bool): Whether to save intermediate AnnData objects.
        progress_callback (callable): A function to report progress. 
                                     It should accept (step, total_steps, message).

    Returns:
        tuple: A tuple containing the processed AnnData object and a dictionary
               of analysis results.
    """
    start_time = time.time()
    
    # Setup output directories
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"scs_results_{timestamp}")
    output_dir = Path(output_dir)
    log_dir = output_dir / "logs"
    checkpoint_dir = output_dir / "intermediate_data"
    metadata_dir = output_dir / "metadata"
    
    for d in [output_dir, log_dir, checkpoint_dir, metadata_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Configure logging for this run
    log_file = log_dir / "analysis_log.txt"
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Add handler to the root logger to capture all logs
    logging.getLogger().addHandler(file_handler)
    
    # --- Pipeline Steps ---
    pipeline_steps = [
        ("calculate_qc", quality_control.calculate_qc_metrics, {}),
        ("filter_cells", quality_control.filter_cells, {"min_genes": min_genes}),
        ("filter_genes", quality_control.filter_genes, {"min_cells": min_cells}),
        ("normalize_data", normalization.log_normalize, {"target_sum": target_sum}),
        ("find_variable_genes", find_variable_genes, {"n_top_genes": n_top_genes}),
        ("scale_data", normalization.scale_data, {}),
        ("run_pca", dimensionality_reduction.run_pca, {"n_comps": n_pcs}),
        ("compute_neighbors", clustering.compute_neighbors, {}),
        ("run_umap", dimensionality_reduction.run_umap, {}),
        ("clustering", clustering.run_leiden_clustering, {"resolution": resolution})
    ]
    total_steps = len(pipeline_steps)

    logger.info(f"Starting standard analysis pipeline with {total_steps} steps.")
    if progress_callback:
        progress_callback(0, total_steps, f"Starting pipeline with {total_steps} steps...")
        
    execution_log = []
    
    # Execute each step
    for i, (name, func, params) in enumerate(pipeline_steps):
        step_start_time = time.time()
        step_num = i + 1
        
        logger.info(f"Executing step {step_num}/{total_steps}: {name}")
        if progress_callback:
            progress_callback(step_num, total_steps, f"Step {step_num}/{total_steps}: {name}...")
            
        try:
            func(adata, **params)
            
            step_duration = time.time() - step_start_time
            execution_log.append({"step": name, "status": "success", "duration_s": step_duration, "error": ""})
            logger.info(f"Step '{name}' completed in {step_duration:.2f}s")
            
            # Save checkpoint if enabled
            if save_checkpoints:
                checkpoint_file = checkpoint_dir / f"{name}.h5ad"
                adata.write(checkpoint_file)
                logger.info(f"Saved key checkpoint: {checkpoint_file}")
                
        except Exception as e:
            step_duration = time.time() - step_start_time
            logger.error(f"Step '{name}' failed after {step_duration:.2f}s: {str(e)}", exc_info=True)
            execution_log.append({"step": name, "status": "failed", "duration_s": step_duration, "error": str(e)})
            
            # Remove file handler and re-raise
            logging.getLogger().removeHandler(file_handler)
            raise e

    total_duration = time.time() - start_time
    logger.info(f"Pipeline completed: {len(pipeline_steps)}/{total_steps} steps successful in {total_duration:.2f}s")
    if progress_callback:
        progress_callback(total_steps, total_steps, "Pipeline finished.")

    # Save final metadata and execution log
    try:
        final_results_path = metadata_dir / "final_adata.h5ad"
        adata.write(final_results_path)
        
        params_used = {
            "min_genes": min_genes, "min_cells": min_cells, "target_sum": target_sum,
            "n_top_genes": n_top_genes, "n_pcs": n_pcs, "resolution": resolution
        }
        with open(metadata_dir / "parameters.json", 'w') as f:
            json.dump(params_used, f, indent=4)
        
        pd.DataFrame(execution_log).to_csv(log_dir / "execution_log.csv", index=False)
        
        logger.info(f"Final metadata saved to: {metadata_dir}")
        logger.info(f"Execution log saved: {log_dir / 'execution_log.csv'}")
        
    except Exception as e:
        logger.error(f"Failed to save final results and metadata: {e}")
        
    logger.info(f"Results saved to: {output_dir}")
    
    # Clean up logger
    logging.getLogger().removeHandler(file_handler)
    
    return adata, {"output_dir": str(output_dir), "execution_log": execution_log}


def create_custom_pipeline(adata, steps_config, name="Custom Pipeline"):
    """
    Create a custom analysis pipeline
    
    Parameters:
    -----------
    adata : anndata.AnnData
        Annotated data object
    steps_config : list
        List of step configurations
    name : str
        Pipeline name
        
    Returns:
    --------
    AnalysisPipeline : Configured pipeline
    """
    pipeline = AnalysisPipeline(adata, name)
    
    for step_config in steps_config:
        pipeline.add_step(
            step_config['name'],
            step_config['function'],
            **step_config.get('kwargs', {})
        )
        
    return pipeline 