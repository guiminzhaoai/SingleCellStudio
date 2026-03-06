"""
Safe import utilities for optional dependencies
"""

import importlib
import sys
from typing import Optional, Any, Dict, List
import logging

logger = logging.getLogger("SingleCellStudio.Dependencies")

def safe_import(package_name: str, module_name: str = None) -> Optional[Any]:
    """
    Safely import optional packages
    
    Args:
        package_name: Name of the package to import
        module_name: Optional specific module within the package
        
    Returns:
        Imported module/package or None if import fails
    """
    try:
        if module_name:
            full_name = f"{package_name}.{module_name}"
            return importlib.import_module(full_name)
        else:
            return importlib.import_module(package_name)
    except ImportError as e:
        logger.debug(f"Optional import failed: {package_name}.{module_name or ''} - {e}")
        return None

def check_package_availability(packages: List[str]) -> Dict[str, bool]:
    """
    Check availability of multiple packages
    
    Args:
        packages: List of package names to check
        
    Returns:
        Dictionary mapping package names to availability status
    """
    availability = {}
    for package in packages:
        if '.' in package:
            # Handle package.module format
            parts = package.split('.')
            main_package = parts[0]
            module_path = '.'.join(parts[1:])
            result = safe_import(main_package, module_path)
        else:
            result = safe_import(package)
        
        availability[package] = result is not None
    
    return availability

def get_package_version(package_name: str) -> Optional[str]:
    """
    Get version of an installed package
    
    Args:
        package_name: Name of the package
        
    Returns:
        Version string or None if package not available
    """
    try:
        module = safe_import(package_name)
        if module is None:
            return None
        
        # Try different version attributes
        for attr in ['__version__', 'version', 'VERSION']:
            if hasattr(module, attr):
                return getattr(module, attr)
        
        # Try importlib.metadata for newer Python versions
        try:
            import importlib.metadata
            return importlib.metadata.version(package_name)
        except ImportError:
            pass
        
        # Try pkg_resources as fallback
        try:
            import pkg_resources
            return pkg_resources.get_distribution(package_name).version
        except:
            pass
            
        return "unknown"
        
    except Exception as e:
        logger.debug(f"Could not get version for {package_name}: {e}")
        return None

# Common optional dependencies for single-cell analysis
OPTIONAL_PACKAGES = {
    'annotation': [
        'celltypist',
        'sctype', 
        'scanpy.external',
    ],
    'trajectory': [
        'scvelo',
        'cellrank',
        'palantir',
        'scanpy.external.pp.magic',
    ],
    'interaction': [
        'squidpy',
        'cellphonedb',
        'commot',
        'stlearn',
    ],
    'visualization': [
        'plotly',
        'bokeh',
        'altair',
    ],
    'spatial': [
        'squidpy',
        'scanpy.external.pl.spatial',
        'stlearn',
    ]
}

def check_category_availability(category: str) -> Dict[str, bool]:
    """
    Check availability of packages in a specific category
    
    Args:
        category: Category name from OPTIONAL_PACKAGES
        
    Returns:
        Dictionary of package availability in that category
    """
    if category not in OPTIONAL_PACKAGES:
        logger.warning(f"Unknown package category: {category}")
        return {}
    
    return check_package_availability(OPTIONAL_PACKAGES[category])

def get_available_categories() -> List[str]:
    """Get list of available package categories"""
    return list(OPTIONAL_PACKAGES.keys()) 