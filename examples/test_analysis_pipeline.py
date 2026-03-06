#!/usr/bin/env python3
"""
Test Analysis Pipeline

This script tests the complete analysis pipeline with real single cell data.
"""

import sys
import os
import argparse
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data import DataLoader
from analysis import StandardPipeline, run_standard_pipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_analysis_pipeline(data_path, output_dir=None):
    """
    Test the complete analysis pipeline
    
    Parameters:
    -----------
    data_path : str
        Path to single cell data
    output_dir : str, optional
        Directory to save results
    """
    logger.info("=" * 60)
    logger.info("SingleCellStudio Analysis Pipeline Test")
    logger.info("=" * 60)
    
    try:
        # Step 1: Load data
        logger.info("Step 1: Loading data...")
        loader = DataLoader()
        adata = loader.load(data_path)
        
        # Get format info
        from data import get_data_info
        data_info = get_data_info(data_path)
        
        logger.info(f"Data loaded successfully:")
        logger.info(f"  - Cells: {adata.n_obs}")
        logger.info(f"  - Genes: {adata.n_vars}")
        logger.info(f"  - Format: {data_info['format']}")
        
        # Step 2: Run standard analysis pipeline
        logger.info("\nStep 2: Running standard analysis pipeline...")
        
        # Configure pipeline parameters
        pipeline_params = {
            'min_genes': 200,        # Minimum genes per cell
            'max_pct_mt': 20,        # Maximum mitochondrial percentage
            'min_cells': 3,          # Minimum cells per gene
            'target_sum': 1e4,       # Normalization target
            'n_top_genes': 2000,     # Number of variable genes
            'n_pcs': 40,             # Number of PCs
            'n_neighbors': 10,       # Neighbors for graph
            'resolution': 0.5,       # Clustering resolution
            'random_state': 42       # For reproducibility
        }
        
        # Create and run pipeline
        pipeline = StandardPipeline(adata, **pipeline_params)
        results = pipeline.execute_pipeline()
        
        # Step 3: Display results
        logger.info("\nStep 3: Analysis Results")
        logger.info("-" * 40)
        
        # Pipeline summary
        logger.info(f"Pipeline: {results['pipeline_name']}")
        logger.info(f"Steps completed: {results['completed_steps']}/{results['total_steps']}")
        logger.info(f"Success rate: {results['success_rate']:.1%}")
        logger.info(f"Total duration: {results['total_duration']:.2f}s")
        
        # Data summary
        if 'data_info' in results:
            data_info = results['data_info']
            logger.info(f"\nFinal Data Summary:")
            logger.info(f"  - Cells after filtering: {data_info['n_cells']}")
            logger.info(f"  - Genes after filtering: {data_info['n_genes']}")
            logger.info(f"  - Variable genes: {data_info['n_variable_genes']}")
            logger.info(f"  - Clusters found: {data_info['n_clusters']}")
            
        # QC metrics
        if 'qc_metrics' in results:
            qc = results['qc_metrics']
            logger.info(f"\nQuality Control Metrics:")
            logger.info(f"  - Mean genes per cell: {qc['mean_genes_per_cell']:.1f}")
            logger.info(f"  - Mean counts per cell: {qc['mean_counts_per_cell']:.1f}")
            logger.info(f"  - Mitochondrial genes: {qc['mt_gene_count']}")
            
        # Filter statistics
        if 'filter_stats' in results:
            filter_stats = results['filter_stats']
            if 'cells' in filter_stats:
                cell_stats = filter_stats['cells']
                logger.info(f"\nCell Filtering:")
                logger.info(f"  - Original: {cell_stats['original']}")
                logger.info(f"  - Filtered: {cell_stats['filtered']}")
                logger.info(f"  - Removed: {cell_stats['removed']}")
                logger.info(f"  - Fraction kept: {cell_stats['fraction_kept']:.1%}")
                
            if 'genes' in filter_stats:
                gene_stats = filter_stats['genes']
                logger.info(f"\nGene Filtering:")
                logger.info(f"  - Original: {gene_stats['original']}")
                logger.info(f"  - Filtered: {gene_stats['filtered']}")
                logger.info(f"  - Removed: {gene_stats['removed']}")
                logger.info(f"  - Fraction kept: {gene_stats['fraction_kept']:.1%}")
        
        # Step execution details
        logger.info(f"\nStep Execution Details:")
        for i, step in enumerate(results['steps']):
            status = "✅" if step['completed'] else "❌"
            duration = f"{step['duration']:.2f}s" if step['duration'] else "N/A"
            logger.info(f"  {i+1}. {step['name']}: {status} ({duration})")
            if step['error']:
                logger.error(f"     Error: {step['error']}")
                
        # Check for key analysis results
        logger.info(f"\nAnalysis Components Available:")
        logger.info(f"  - Raw data: {'✅' if adata.raw is not None else '❌'}")
        logger.info(f"  - PCA: {'✅' if 'X_pca' in adata.obsm else '❌'}")
        logger.info(f"  - UMAP: {'✅' if 'X_umap' in adata.obsm else '❌'}")
        logger.info(f"  - Clusters: {'✅' if 'leiden' in adata.obs else '❌'}")
        logger.info(f"  - Neighbors: {'✅' if 'neighbors' in adata.uns else '❌'}")
        
        # Save results if output directory specified
        if output_dir:
            logger.info(f"\nSaving results to {output_dir}...")
            os.makedirs(output_dir, exist_ok=True)
            
            # Save AnnData object
            adata_path = os.path.join(output_dir, "analysis_results.h5ad")
            adata.write(adata_path)
            logger.info(f"  - AnnData saved: {adata_path}")
            
            # Save pipeline summary
            import json
            summary_path = os.path.join(output_dir, "pipeline_summary.json")
            with open(summary_path, 'w') as f:
                # Convert datetime objects to strings for JSON serialization
                json_results = results.copy()
                for key in ['start_time', 'end_time']:
                    if json_results[key]:
                        json_results[key] = json_results[key].isoformat()
                for log_entry in json_results['execution_log']:
                    log_entry['timestamp'] = log_entry['timestamp'].isoformat()
                    
                json.dump(json_results, f, indent=2, default=str)
            logger.info(f"  - Pipeline summary saved: {summary_path}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Analysis pipeline test completed successfully!")
        logger.info("=" * 60)
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Analysis pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test SingleCellStudio Analysis Pipeline")
    parser.add_argument("data_path", help="Path to single cell data file or folder")
    parser.add_argument("-o", "--output", help="Output directory for results")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Test the analysis pipeline
    results = test_analysis_pipeline(args.data_path, args.output)
    
    if results is None:
        sys.exit(1)
    else:
        print(f"\n🎉 Success! Analysis completed with {results['success_rate']:.1%} success rate.")
        if args.output:
            print(f"📁 Results saved to: {args.output}")


if __name__ == "__main__":
    main() 