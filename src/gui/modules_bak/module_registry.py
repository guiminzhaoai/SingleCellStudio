"""
GUI Module Registry

Central registry for managing GUI modules in SingleCellStudio.
This allows for modular, plugin-like architecture where new modules
can be added without modifying the main window code.
"""

from typing import Dict, List, Optional, Type, Any
from abc import ABC, abstractmethod
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class BaseGUIModule(ABC):
    """Base class for all GUI modules"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.logger = logging.getLogger(self.__class__.__name__)
        self._widget = None
        self._enabled = True
        # Data manager will be set by the main window
        self.data_manager = None
    
    @property
    @abstractmethod
    def module_name(self) -> str:
        """Unique name for this module"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for display"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of module functionality"""
        pass
    
    @property
    def version(self) -> str:
        """Module version"""
        return "1.0.0"
    
    @property
    def requirements(self) -> List[str]:
        """List of required dependencies"""
        return []
    
    @property
    def enabled(self) -> bool:
        """Whether module is enabled"""
        return self._enabled
    
    @abstractmethod
    def create_widget(self, parent=None):
        """Create and return the main widget for this module"""
        pass
    
    def initialize(self):
        """Initialize the module (called once during registration)"""
        pass
    
    def cleanup(self):
        """Cleanup resources when module is destroyed"""
        pass
    
    def set_data(self, adata):
        """Set analysis data for the module"""
        pass
    
    def get_menu_actions(self) -> List[Dict[str, Any]]:
        """Return list of menu actions this module provides
        
        Returns:
            List of dicts with keys: 'text', 'callback', 'shortcut' (optional)
        """
        return []
    
    def get_toolbar_actions(self) -> List[Dict[str, Any]]:
        """Return list of toolbar actions this module provides"""
        return []

class ModuleRegistry:
    """Central registry for GUI modules"""
    
    def __init__(self):
        self._modules: Dict[str, BaseGUIModule] = {}
        self._module_classes: Dict[str, Type[BaseGUIModule]] = {}
        self._tab_modules: List[str] = []  # Modules that provide tabs
        self._panel_modules: List[str] = []  # Modules that provide panels
        self.logger = logging.getLogger(__name__)
    
    def register_module_class(self, module_class: Type[BaseGUIModule]):
        """Register a module class (not instantiated yet)"""
        if not issubclass(module_class, BaseGUIModule):
            raise ValueError(f"Module class must inherit from BaseGUIModule")
        
        # Create temporary instance to get module name
        temp_instance = module_class()
        module_name = temp_instance.module_name
        
        if module_name in self._module_classes:
            self.logger.warning(f"Module {module_name} already registered, overwriting")
        
        self._module_classes[module_name] = module_class
        self.logger.info(f"Registered module class: {module_name}")
    
    def instantiate_module(self, module_name: str, parent=None) -> Optional[BaseGUIModule]:
        """Create an instance of a registered module"""
        if module_name not in self._module_classes:
            self.logger.error(f"Module {module_name} not found in registry")
            return None
        
        try:
            module_class = self._module_classes[module_name]
            instance = module_class(parent)
            
            # Check requirements
            missing_deps = self._check_requirements(instance)
            if missing_deps:
                self.logger.warning(f"Module {module_name} missing dependencies: {missing_deps}")
                instance._enabled = False
            
            # Initialize
            instance.initialize()
            
            self._modules[module_name] = instance
            self.logger.info(f"Instantiated module: {module_name}")
            return instance
            
        except Exception as e:
            self.logger.error(f"Failed to instantiate module {module_name}: {e}")
            return None
    
    def get_module(self, module_name: str) -> Optional[BaseGUIModule]:
        """Get an instantiated module"""
        return self._modules.get(module_name)
    
    def get_all_modules(self) -> Dict[str, BaseGUIModule]:
        """Get all instantiated modules"""
        return self._modules.copy()
    
    def get_enabled_modules(self) -> Dict[str, BaseGUIModule]:
        """Get only enabled modules"""
        return {name: module for name, module in self._modules.items() if module.enabled}
    
    def register_tab_module(self, module_name: str):
        """Register a module as providing a tab"""
        if module_name not in self._tab_modules:
            self._tab_modules.append(module_name)
    
    def register_panel_module(self, module_name: str):
        """Register a module as providing a panel"""
        if module_name not in self._panel_modules:
            self._panel_modules.append(module_name)
    
    def get_tab_modules(self) -> List[str]:
        """Get list of modules that provide tabs"""
        return self._tab_modules.copy()
    
    def get_panel_modules(self) -> List[str]:
        """Get list of modules that provide panels"""
        return self._panel_modules.copy()
    
    def auto_discover_modules(self, modules_dir: Path):
        """Auto-discover and register modules from a directory"""
        if not modules_dir.exists():
            self.logger.warning(f"Modules directory not found: {modules_dir}")
            return
        
        discovered = 0
        for module_file in modules_dir.glob("*_module.py"):
            try:
                # Import module dynamically
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    module_file.stem, module_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for classes that inherit from BaseGUIModule
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseGUIModule) and 
                        attr != BaseGUIModule):
                        
                        self.register_module_class(attr)
                        discovered += 1
                        
            except Exception as e:
                self.logger.error(f"Failed to discover module {module_file}: {e}")
        
        self.logger.info(f"Auto-discovered {discovered} modules")
    
    def _check_requirements(self, module: BaseGUIModule) -> List[str]:
        """Check if module requirements are met"""
        missing = []
        for req in module.requirements:
            try:
                __import__(req)
            except ImportError:
                missing.append(req)
        return missing
    
    def cleanup_all(self):
        """Cleanup all modules"""
        for module in self._modules.values():
            try:
                module.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up module {module.module_name}: {e}")
        
        self._modules.clear()
        self.logger.info("All modules cleaned up")

# Global registry instance
registry = ModuleRegistry() 