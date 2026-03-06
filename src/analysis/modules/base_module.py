"""
Base module class for all analysis modules in SingleCellStudio
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

@dataclass
class ModuleParameter:
    """Configuration parameter for analysis modules"""
    name: str
    display_name: str
    param_type: type
    default_value: Any
    description: str
    options: Optional[List[Any]] = None  # For dropdown parameters
    min_value: Optional[float] = None    # For numeric parameters
    max_value: Optional[float] = None    # For numeric parameters

class AnalysisModule(ABC):
    """
    Abstract base class for all analysis modules
    
    This class defines the interface that all analysis modules must implement
    to be compatible with the SingleCellStudio modular architecture.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"SingleCellStudio.{self.__class__.__name__}")
        self._is_available = None  # Cache availability check
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Module display name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of what this module does"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Module version"""
        pass
    
    @property
    @abstractmethod
    def required_dependencies(self) -> List[str]:
        """Required Python packages for basic functionality"""
        pass
    
    @property
    @abstractmethod
    def optional_dependencies(self) -> List[str]:
        """Optional packages for enhanced functionality"""
        pass
    
    @property
    @abstractmethod
    def required_data_keys(self) -> List[str]:
        """Required keys in adata.obs or adata.var for this module to work"""
        pass
    
    def is_available(self) -> bool:
        """
        Check if module can run with current dependencies
        Caches result to avoid repeated import checks
        """
        if self._is_available is None:
            self._is_available = self._check_dependencies()
        return self._is_available
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        try:
            for dep in self.required_dependencies:
                # Try to import each required dependency
                if '.' in dep:
                    package, module = dep.split('.', 1)
                    __import__(f"{package}.{module}", fromlist=[module])
                else:
                    __import__(dep)
            return True
        except ImportError as e:
            self.logger.warning(f"Module {self.name} unavailable: {e}")
            return False
    
    def get_available_methods(self) -> List[str]:
        """Get list of available analysis methods for this module"""
        methods = ['basic']  # Always have a basic fallback method
        
        # Check optional dependencies and add corresponding methods
        for dep in self.optional_dependencies:
            try:
                if '.' in dep:
                    package, module = dep.split('.', 1)
                    __import__(f"{package}.{module}", fromlist=[module])
                else:
                    __import__(dep)
                methods.append(dep.lower())
            except ImportError:
                continue
        
        return methods
    
    @abstractmethod
    def get_parameters(self) -> List[ModuleParameter]:
        """Get configurable parameters for this module"""
        pass
    
    @abstractmethod
    def validate_data(self, adata) -> Tuple[bool, str]:
        """
        Validate that the input data is suitable for this module
        
        Returns:
            (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def run_analysis(self, adata, method: str = 'auto', **kwargs) -> Dict[str, Any]:
        """
        Execute the analysis
        
        Args:
            adata: AnnData object with single-cell data
            method: Analysis method to use ('auto', 'basic', or specific method)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with analysis results
        """
        pass
    
    def get_result_description(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable description of the results"""
        return f"Analysis completed using {self.name} module"
    
    def get_visualization_options(self) -> List[str]:
        """Get available visualization types for this module's results"""
        return ['summary']  # Default visualization
    
    def create_visualization(self, adata, results: Dict[str, Any], 
                           plot_type: str = 'summary', **kwargs) -> Any:
        """
        Create visualization for the analysis results
        
        Args:
            adata: AnnData object
            results: Results from run_analysis
            plot_type: Type of plot to create
            **kwargs: Additional plotting parameters
            
        Returns:
            Matplotlib figure or similar plot object
        """
        # Default implementation - subclasses should override
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, f"{self.name}\nVisualization not implemented", 
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title(f"{self.name} Results")
        return fig 