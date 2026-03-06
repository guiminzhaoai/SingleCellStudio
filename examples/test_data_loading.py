#!/usr/bin/env python3
"""
Test Data Loading for SingleCellStudio

This script demonstrates how to load single cell RNA-seq data
using the SingleCellStudio data loading modules.

Usage:
    python test_data_loading.py [data_path]
"""

import sys
import os
from pathlib import Path
import logging

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data import DataLoader, DataFormat, get_data_info, auto_detect_format
from data.validators import DataValidator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_data_loading(data_path: str):
    """Test data loading functionality"""
    
    print("=" * 60)
    print("SingleCellStudio Data Loading Test")
    print("=" * 60)
    
    data_path = Path(data_path)
    
    # Step 1: Check if data exists
    print(f"\n1. Checking data path: {data_path}")
    if not data_path.exists():
        print(f"❌ Data path does not exist: {data_path}")
        return False
    
    print(f"✅ Data path exists")
    
    # Step 2: Get data info without loading
    print(f"\n2. Getting data information...")
    try:
        info = get_data_info(data_path)
        print(f"   📊 Format: {info['format']}")
        print(f"   📁 Path: {info['path']}")
        print(f"   📏 Size: {info.get('size_mb', 'Unknown')} MB")
        
        if info.get('n_cells'):
            print(f"   🧬 Cells: {info['n_cells']:,}")
        if info.get('n_genes'):
            print(f"   🧬 Genes: {info['n_genes']:,}")
        
        if info.get('error'):
            print(f"   ⚠️  Error: {info['error']}")
            
    except Exception as e:
        print(f"❌ Error getting data info: {e}")
        return False
    
    # Step 3: Auto-detect format
    print(f"\n3. Auto-detecting format...")
    try:
        detected_format = auto_detect_format(data_path)
        print(f"   🔍 Detected format: {detected_format.value}")
    except Exception as e:
        print(f"❌ Error detecting format: {e}")
        return False
    
    # Step 4: Load data
    print(f"\n4. Loading data...")
    try:
        loader = DataLoader()
        adata = loader.load(data_path)
        
        print(f"   ✅ Successfully loaded data!")
        print(f"   📊 Shape: {adata.n_obs:,} cells × {adata.n_vars:,} genes")
        print(f"   🧬 Matrix type: {'sparse' if hasattr(adata.X, 'nnz') else 'dense'}")
        
        # Show some basic info
        if hasattr(adata.X, 'nnz'):
            sparsity = 1.0 - (adata.X.nnz / (adata.n_obs * adata.n_vars))
            print(f"   📈 Sparsity: {sparsity:.1%}")
        
        # Show metadata
        if 'scs_metadata' in adata.uns:
            metadata = adata.uns['scs_metadata']
            print(f"   📅 Loaded at: {metadata['loaded_at']}")
            print(f"   📁 Source format: {metadata['format']}")
        
        # Show sample cell and gene names
        print(f"\n   Sample cell barcodes:")
        for i, barcode in enumerate(adata.obs_names[:3]):
            print(f"     {i+1}. {barcode}")
        
        print(f"\n   Sample gene names:")
        for i, gene in enumerate(adata.var_names[:3]):
            print(f"     {i+1}. {gene}")
        
        # Show gene metadata if available
        if len(adata.var.columns) > 0:
            print(f"\n   Gene metadata columns: {list(adata.var.columns)}")
            
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Validate data
    print(f"\n5. Validating data quality...")
    try:
        validator = DataValidator()
        validation_results = validator.validate_adata(adata)
        
        if validation_results['valid']:
            print(f"   ✅ Data validation passed!")
        else:
            print(f"   ⚠️  Data validation found issues")
        
        # Show summary
        n_errors = validation_results['info'].get('n_errors', 0)
        n_warnings = validation_results['info'].get('n_warnings', 0)
        print(f"   📊 Errors: {n_errors}, Warnings: {n_warnings}")
        
        # Show key metrics
        info = validation_results['info']
        if 'mean_genes_per_cell' in info:
            print(f"   📈 Mean genes per cell: {info['mean_genes_per_cell']:.0f}")
        if 'sparsity' in info:
            print(f"   📈 Data sparsity: {info['sparsity']:.1%}")
        
        # Show errors and warnings
        if validation_results['errors']:
            print(f"\n   ❌ Errors:")
            for error in validation_results['errors']:
                print(f"     • {error}")
        
        if validation_results['warnings']:
            print(f"\n   ⚠️  Warnings:")
            for warning in validation_results['warnings'][:5]:  # Show first 5
                print(f"     • {warning}")
            if len(validation_results['warnings']) > 5:
                print(f"     ... and {len(validation_results['warnings']) - 5} more warnings")
        
        # Show recommendations
        if validation_results['recommendations']:
            print(f"\n   💡 Recommendations:")
            for rec in validation_results['recommendations']:
                print(f"     • {rec}")
                
    except Exception as e:
        print(f"❌ Error validating data: {e}")
        return False
    
    print(f"\n🎉 Data loading test completed successfully!")
    return True

def show_usage():
    """Show usage information"""
    print("SingleCellStudio Data Loading Test")
    print()
    print("Usage:")
    print("  python test_data_loading.py <data_path>")
    print()
    print("Supported formats:")
    print("  • 10X Genomics MTX folder (with matrix.mtx.gz, barcodes.tsv.gz, features.tsv.gz)")
    print("  • 10X Genomics H5 file (.h5)")
    print("  • AnnData H5AD file (.h5ad)")
    print("  • CSV/TSV files")
    print()
    print("Examples:")
    print("  python test_data_loading.py /path/to/filtered_feature_bc_matrix/")
    print("  python test_data_loading.py /path/to/filtered_feature_bc_matrix.h5")
    print("  python test_data_loading.py /path/to/data.h5ad")

def main():
    """Main function"""
    
    if len(sys.argv) != 2:
        show_usage()
        return
    
    data_path = sys.argv[1]
    
    # Test the data loading
    success = test_data_loading(data_path)
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 