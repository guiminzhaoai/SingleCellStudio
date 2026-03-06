"""
Advanced analysis modules for SingleCellStudio

This package contains modular analysis components that extend the core pipeline
with advanced single-cell analysis capabilities.
"""

from .base_module import AnalysisModule
from .registry import ModuleRegistry

__all__ = ['AnalysisModule', 'ModuleRegistry'] 