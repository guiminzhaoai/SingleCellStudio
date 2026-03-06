"""
Data Format Specifications for SingleCellStudio

This module defines supported data formats and provides utilities
for format detection and validation.
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DataFormat(Enum):
    """Supported data formats for single cell RNA-seq data"""
    
    # 10X Genomics formats
    TENX_MTX = "10x_mtx"           # MTX + TSV files in folder
    TENX_H5 = "10x_h5"             # 10X HDF5 format
    
    # Standard formats
    H5AD = "h5ad"                  # AnnData HDF5 format
    CSV = "csv"                    # Comma-separated values
    TSV = "tsv"                    # Tab-separated values
    EXCEL = "excel"                # Excel spreadsheet
    
    # Compressed formats
    CSV_GZ = "csv_gz"              # Gzipped CSV
    TSV_GZ = "tsv_gz"              # Gzipped TSV
    
    # Other formats
    LOOM = "loom"                  # Loom format
    ZARR = "zarr"                  # Zarr format
    
    UNKNOWN = "unknown"            # Unknown/unsupported format

class FormatSpec:
    """Specification for a data format"""
    
    def __init__(self, 
                 format_type: DataFormat,
                 extensions: List[str],
                 description: str,
                 requires_folder: bool = False,
                 required_files: Optional[List[str]] = None):
        self.format_type = format_type
        self.extensions = extensions
        self.description = description
        self.requires_folder = requires_folder
        self.required_files = required_files or []

# Format specifications
FORMAT_SPECS = {
    DataFormat.TENX_MTX: FormatSpec(
        format_type=DataFormat.TENX_MTX,
        extensions=[],  # No single extension, it's a folder
        description="10X Genomics MTX format (folder with matrix.mtx.gz, barcodes.tsv.gz, features.tsv.gz)",
        requires_folder=True,
        required_files=["matrix.mtx.gz", "barcodes.tsv.gz", "features.tsv.gz"]
    ),
    
    DataFormat.TENX_H5: FormatSpec(
        format_type=DataFormat.TENX_H5,
        extensions=[".h5", ".hdf5"],
        description="10X Genomics HDF5 format"
    ),
    
    DataFormat.H5AD: FormatSpec(
        format_type=DataFormat.H5AD,
        extensions=[".h5ad"],
        description="AnnData HDF5 format"
    ),
    
    DataFormat.CSV: FormatSpec(
        format_type=DataFormat.CSV,
        extensions=[".csv"],
        description="Comma-separated values"
    ),
    
    DataFormat.TSV: FormatSpec(
        format_type=DataFormat.TSV,
        extensions=[".tsv", ".txt"],
        description="Tab-separated values"
    ),
    
    DataFormat.EXCEL: FormatSpec(
        format_type=DataFormat.EXCEL,
        extensions=[".xlsx", ".xls"],
        description="Excel spreadsheet"
    ),
    
    DataFormat.CSV_GZ: FormatSpec(
        format_type=DataFormat.CSV_GZ,
        extensions=[".csv.gz"],
        description="Gzipped CSV"
    ),
    
    DataFormat.TSV_GZ: FormatSpec(
        format_type=DataFormat.TSV_GZ,
        extensions=[".tsv.gz", ".txt.gz"],
        description="Gzipped TSV"
    ),
    
    DataFormat.LOOM: FormatSpec(
        format_type=DataFormat.LOOM,
        extensions=[".loom"],
        description="Loom format"
    ),
    
    DataFormat.ZARR: FormatSpec(
        format_type=DataFormat.ZARR,
        extensions=[".zarr"],
        description="Zarr format",
        requires_folder=True
    )
}

def get_supported_formats() -> Dict[DataFormat, FormatSpec]:
    """Get all supported data formats"""
    return FORMAT_SPECS.copy()

def detect_file_format(file_path: Path) -> DataFormat:
    """
    Detect the format of a data file or folder
    
    Args:
        file_path: Path to file or folder
        
    Returns:
        Detected DataFormat
    """
    file_path = Path(file_path)
    
    # Check if it's a folder (10X MTX format)
    if file_path.is_dir():
        return _detect_folder_format(file_path)
    
    # Check file extension
    return _detect_file_format_by_extension(file_path)

def _detect_folder_format(folder_path: Path) -> DataFormat:
    """Detect format for a folder"""
    
    # Check for 10X MTX format
    required_files = FORMAT_SPECS[DataFormat.TENX_MTX].required_files
    
    if all((folder_path / file).exists() for file in required_files):
        logger.info(f"Detected 10X MTX format in folder: {folder_path}")
        return DataFormat.TENX_MTX
    
    # Check for alternative 10X file names
    alt_files = ["matrix.mtx", "barcodes.tsv", "features.tsv"]
    if all((folder_path / file).exists() for file in alt_files):
        logger.info(f"Detected 10X MTX format (uncompressed) in folder: {folder_path}")
        return DataFormat.TENX_MTX
    
    # Check for older 10X format (genes.tsv instead of features.tsv)
    old_files = ["matrix.mtx.gz", "barcodes.tsv.gz", "genes.tsv.gz"]
    if all((folder_path / file).exists() for file in old_files):
        logger.info(f"Detected 10X MTX format (legacy) in folder: {folder_path}")
        return DataFormat.TENX_MTX
    
    # Check for Zarr format
    if (folder_path / ".zarray").exists() or (folder_path / ".zgroup").exists():
        logger.info(f"Detected Zarr format in folder: {folder_path}")
        return DataFormat.ZARR
    
    logger.warning(f"Unknown folder format: {folder_path}")
    return DataFormat.UNKNOWN

def _detect_file_format_by_extension(file_path: Path) -> DataFormat:
    """Detect format by file extension"""
    
    # Get file extension (including compound extensions like .csv.gz)
    name = file_path.name.lower()
    
    # Check compound extensions first
    for format_type, spec in FORMAT_SPECS.items():
        for ext in spec.extensions:
            if name.endswith(ext.lower()):
                logger.info(f"Detected {format_type.value} format: {file_path}")
                return format_type
    
    logger.warning(f"Unknown file format: {file_path}")
    return DataFormat.UNKNOWN

def validate_format_requirements(file_path: Path, expected_format: DataFormat) -> bool:
    """
    Validate that a file/folder meets the requirements for the expected format
    
    Args:
        file_path: Path to validate
        expected_format: Expected data format
        
    Returns:
        True if requirements are met
    """
    if expected_format not in FORMAT_SPECS:
        logger.error(f"Unknown format: {expected_format}")
        return False
    
    spec = FORMAT_SPECS[expected_format]
    file_path = Path(file_path)
    
    # Check if path exists
    if not file_path.exists():
        logger.error(f"Path does not exist: {file_path}")
        return False
    
    # Check folder requirements
    if spec.requires_folder:
        if not file_path.is_dir():
            logger.error(f"Format {expected_format.value} requires a folder, got file: {file_path}")
            return False
        
        # Check required files in folder
        for required_file in spec.required_files:
            if not (file_path / required_file).exists():
                logger.error(f"Missing required file {required_file} in {file_path}")
                return False
    else:
        if file_path.is_dir():
            logger.error(f"Format {expected_format.value} requires a file, got folder: {file_path}")
            return False
    
    logger.info(f"Format validation passed for {expected_format.value}: {file_path}")
    return True

def get_format_description(format_type: DataFormat) -> str:
    """Get human-readable description of a format"""
    if format_type in FORMAT_SPECS:
        return FORMAT_SPECS[format_type].description
    return "Unknown format"

def get_format_extensions(format_type: DataFormat) -> List[str]:
    """Get file extensions for a format"""
    if format_type in FORMAT_SPECS:
        return FORMAT_SPECS[format_type].extensions
    return []

def is_supported_format(format_type: DataFormat) -> bool:
    """Check if a format is supported"""
    return format_type in FORMAT_SPECS and format_type != DataFormat.UNKNOWN 