"""
SingleCellStudio Version Information
"""

__version__ = "0.2.0"
__version_info__ = (0, 2, 0)

# Build information
__build__ = "alpha"
__commit__ = "data-loading-complete"

# Release information
__release_name__ = "Data Loading Alpha"
__release_date__ = "2024-12-21"

# API version for compatibility checking
__api_version__ = "1.0"

# Minimum supported versions
MIN_PYTHON_VERSION = (3, 8)
MIN_PYQT_VERSION = "6.5.0"
MIN_SCANPY_VERSION = "1.9.0"

def get_version_string():
    """Get formatted version string"""
    if __build__ == "dev":
        return f"{__version__}-{__build__}"
    return __version__

def get_full_version_info():
    """Get complete version information"""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "build": __build__,
        "commit": __commit__,
        "release_name": __release_name__,
        "release_date": __release_date__,
        "api_version": __api_version__,
    }

# Version string for display
VERSION_STRING = get_version_string() 