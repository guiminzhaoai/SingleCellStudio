"""
SingleCellStudio - Commercial Single Cell Transcriptome Analysis Software

A professional-grade, Windows-based platform for single cell RNA-seq analysis
that rivals industry leaders like CLC Workbench.
"""

from .version import __version__, VERSION_STRING, get_full_version_info

# Package metadata
__title__ = "SingleCellStudio"
__description__ = "Commercial Single Cell Transcriptome Analysis Software"
__author__ = "SingleCellStudio Inc."
__email__ = "info@singlecellstudio.com"
__license__ = "Commercial"
__copyright__ = "Copyright 2024 SingleCellStudio Inc."

# Export main components (when implemented)
__all__ = [
    "__version__",
    "VERSION_STRING", 
    "get_full_version_info",
]

# Lazy imports for better startup performance
def get_main_window():
    """Lazy import of main window to avoid circular imports"""
    from .gui.main_window import MainWindow
    return MainWindow

def get_analysis_engine():
    """Lazy import of analysis engine"""
    from .analysis.engine import AnalysisEngine
    return AnalysisEngine

def get_data_manager():
    """Lazy import of data manager"""
    from .data.manager import DataManager
    return DataManager

"""
SingleCellStudio source package
""" 