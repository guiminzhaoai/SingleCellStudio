"""
Dependency management utilities for SingleCellStudio

This package provides safe import handling and dependency checking
to gracefully handle optional packages.
"""

try:
    from .optional_imports import safe_import, check_package_availability
    from .checker import DependencyChecker
    
    __all__ = ['safe_import', 'check_package_availability', 'DependencyChecker']
except ImportError:
    # Fallback for when imports fail
    __all__ = [] 