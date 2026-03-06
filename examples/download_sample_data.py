#!/usr/bin/env python3
"""
Download sample data for SingleCellStudio examples.

This script downloads the 10X scRNA-seq dataset used in testing and development.
The sample data is too large to include in the GitHub repository, so this script
provides an easy way to obtain the necessary files for running examples.

Usage:
    python download_sample_data.py

The script will create a 'sample_data' directory and download:
- filtered_feature_bc_matrix.h5 (HDF5 format)
- filtered_feature_bc_matrix/ (MTX format directory)
"""

import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
import zipfile
import gzip
import shutil

def download_with_progress(url, filepath):
    """Download file with progress indicator."""
    def progress_hook(block_num, block_size, total_size):
        if total_size > 0:
            percent = min(100, (block_num * block_size * 100) // total_size)
            sys.stdout.write(f"\r  Progress: {percent}% ({block_num * block_size // 1024} KB)")
            sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, filepath, reporthook=progress_hook)
        print()  # New line after progress
        return True
    except urllib.error.URLError as e:
        print(f"\n❌ Error downloading: {e}")
        return False

def download_sample_data():
    """Download sample scRNA-seq data from 10X Genomics."""
    
    print("🧬 SingleCellStudio Sample Data Downloader")
    print("=" * 50)
    
    # Create sample_data directory
    data_dir = Path("sample_data")
    data_dir.mkdir(exist_ok=True)
    
    print(f"📁 Data directory: {data_dir.absolute()}")
    
    # 10X Genomics public datasets
    # Using PBMC 1k dataset (smaller for testing)
    base_url = "https://cf.10xgenomics.com/samples/cell-exp/3.0.0/pbmc_1k_v3"
    
    files_to_download = {
        "filtered_feature_bc_matrix.h5": f"{base_url}/pbmc_1k_v3_filtered_feature_bc_matrix.h5",
        "filtered_feature_bc_matrix.tar.gz": f"{base_url}/pbmc_1k_v3_filtered_feature_bc_matrix.tar.gz"
    }
    
    downloaded_files = []
    
    for filename, url in files_to_download.items():
        filepath = data_dir / filename
        
        if filepath.exists():
            print(f"⏭️  {filename} already exists ({filepath.stat().st_size // 1024} KB)")
            downloaded_files.append(filepath)
            continue
        
        print(f"📥 Downloading {filename}...")
        print(f"   URL: {url}")
        
        if download_with_progress(url, filepath):
            size_kb = filepath.stat().st_size // 1024
            print(f"✅ Downloaded {filename} ({size_kb} KB)")
            downloaded_files.append(filepath)
        else:
            print(f"❌ Failed to download {filename}")
    
    # Extract MTX format if tar.gz was downloaded
    tar_file = data_dir / "filtered_feature_bc_matrix.tar.gz"
    mtx_dir = data_dir / "filtered_feature_bc_matrix"
    
    if tar_file.exists() and not mtx_dir.exists():
        print("📦 Extracting MTX format files...")
        try:
            import tarfile
            with tarfile.open(tar_file, 'r:gz') as tar:
                tar.extractall(data_dir)
            print("✅ MTX format extracted")
            
            # Clean up tar file
            tar_file.unlink()
            print("🗑️  Cleaned up tar.gz file")
            
        except Exception as e:
            print(f"❌ Error extracting MTX files: {e}")
    
    # Verify downloaded files
    print("\n🔍 Verifying downloaded files:")
    
    h5_file = data_dir / "filtered_feature_bc_matrix.h5"
    if h5_file.exists():
        try:
            import h5py
            with h5py.File(h5_file, 'r') as f:
                print(f"✅ HDF5 file valid - Groups: {list(f.keys())}")
        except ImportError:
            print("⚠️  h5py not installed - cannot verify HDF5 file")
        except Exception as e:
            print(f"❌ HDF5 file verification failed: {e}")
    
    if mtx_dir.exists():
        required_files = ['matrix.mtx.gz', 'barcodes.tsv.gz', 'features.tsv.gz']
        missing_files = [f for f in required_files if not (mtx_dir / f).exists()]
        
        if not missing_files:
            print("✅ MTX format complete - All required files present")
        else:
            print(f"⚠️  MTX format incomplete - Missing: {missing_files}")
    
    # Create README for the data
    readme_content = """# Sample Data for SingleCellStudio

This directory contains sample single cell RNA-seq data for testing and examples.

## Dataset Information

**Source:** 10X Genomics
**Dataset:** 1k PBMCs from a Healthy Donor (v3 chemistry)
**Cells:** ~1,000 peripheral blood mononuclear cells
**Genes:** ~33,000 genes

## File Formats

### HDF5 Format
- `filtered_feature_bc_matrix.h5` - Complete dataset in HDF5 format

### MTX Format  
- `filtered_feature_bc_matrix/` - Directory containing:
  - `matrix.mtx.gz` - Count matrix (genes x cells)
  - `barcodes.tsv.gz` - Cell barcodes
  - `features.tsv.gz` - Gene information

## Usage

Load this data in SingleCellStudio by:
1. Launching the application
2. Clicking "Import Data"
3. Selecting either the .h5 file or the MTX directory
4. Following the import wizard

## Citation

If you use this data in publications, please cite:
- 10X Genomics (2019). 1k PBMCs from a Healthy Donor (v3 chemistry). 
  Single Cell Gene Expression Dataset by Cell Ranger 3.0.0.

## License

This sample data is provided by 10X Genomics for educational and research purposes.
Please refer to 10X Genomics terms of use for commercial applications.
"""
    
    readme_path = data_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"📝 Created {readme_path}")
    
    print("\n🎉 Sample data setup complete!")
    print(f"📊 Data location: {data_dir.absolute()}")
    print("🚀 You can now run SingleCellStudio examples with this data.")
    
    return len(downloaded_files) > 0

if __name__ == "__main__":
    success = download_sample_data()
    if not success:
        print("\n⚠️  Some downloads failed. You may need to:")
        print("   1. Check your internet connection")
        print("   2. Try running the script again")
        print("   3. Download files manually from 10X Genomics website")
        sys.exit(1) 