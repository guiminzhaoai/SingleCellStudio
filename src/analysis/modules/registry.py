"""
Module registry system for SingleCellStudio analysis modules
"""

from typing import Dict, List, Optional, Type
import logging
import importlib
import inspect
from pathlib import Path

from .base_module import AnalysisModule

# Try to import dependency checker, fallback if not available
try:
    from ...dependencies import DependencyChecker
except ImportError:
    # Create a dummy dependency checker if import fails
    class DependencyChecker:
        def __init__(self):
            pass
        def check_module_dependencies(self, required, optional=None):
            return {'available': True, 'missing_required': [], 'available_optional': [], 'missing_optional': []}
        def get_system_report(self):
            return {'core_dependencies': {}, 'optional_categories': {}, 'recommendations': [], 'warnings': []}
        def clear_cache(self):
            pass

logger = logging.getLogger("SingleCellStudio.ModuleRegistry")

class ModuleRegistry:
    """
    Central registry for all analysis modules
    
    This class manages discovery, registration, and access to analysis modules.
    It automatically discovers modules in the modules directory and provides
    access to available modules based on current dependencies.
    """
    
    def __init__(self):
        self._modules: Dict[str, AnalysisModule] = {}
        self._module_classes: Dict[str, Type[AnalysisModule]] = {}
        self.dependency_checker = DependencyChecker()
        self._load_modules()
    
    def _load_modules(self):
        """Automatically discover and load all analysis modules"""
        try:
            # Get the modules directory path
            modules_dir = Path(__file__).parent
            
            # Find all Python files that could contain modules
            for module_file in modules_dir.rglob("*.py"):
                if module_file.name.startswith('_') or module_file.name == 'base_module.py':
                    continue
                
                # Convert file path to module path
                relative_path = module_file.relative_to(modules_dir.parent.parent.parent)
                module_path = str(relative_path.with_suffix('')).replace('/', '.').replace('\\', '.')
                
                try:
                    self._load_module_from_path(module_path)
                except Exception as e:
                    logger.debug(f"Could not load module from {module_path}: {e}")
            
            logger.info(f"Loaded {len(self._modules)} analysis modules")
            
        except Exception as e:
            logger.error(f"Error loading modules: {e}")
    
    def _load_module_from_path(self, module_path: str):
        """Load a specific module from its path"""
        try:
            module = importlib.import_module(module_path)
            
            # Find AnalysisModule subclasses in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, AnalysisModule) and 
                    obj != AnalysisModule and 
                    not inspect.isabstract(obj)):
                    
                    # Create instance and register
                    try:
                        instance = obj()
                        self.register_module(instance)
                        logger.debug(f"Registered module: {instance.name}")
                    except Exception as e:
                        logger.warning(f"Could not instantiate module {name}: {e}")
                        
        except Exception as e:
            logger.debug(f"Could not import module {module_path}: {e}")
    
    def register_module(self, module: AnalysisModule):
        """
        Register an analysis module
        
        Args:
            module: Instance of AnalysisModule to register
        """
        if not isinstance(module, AnalysisModule):
            raise ValueError(f"Module must be instance of AnalysisModule, got {type(module)}")
        
        module_name = module.name.lower().replace(' ', '_')
        self._modules[module_name] = module
        self._module_classes[module_name] = module.__class__
        
        logger.debug(f"Registered module: {module.name} ({module_name})")
    
    def get_module(self, name: str) -> Optional[AnalysisModule]:
        """
        Get a specific module by name
        
        Args:
            name: Module name (case insensitive)
            
        Returns:
            Module instance or None if not found
        """
        normalized_name = name.lower().replace(' ', '_')
        return self._modules.get(normalized_name)
    
    def get_available_modules(self) -> Dict[str, AnalysisModule]:
        """
        Get all modules that can run with current dependencies
        
        Returns:
            Dictionary mapping module names to available module instances
        """
        available = {}
        for name, module in self._modules.items():
            if module.is_available():
                available[name] = module
            else:
                logger.debug(f"Module {module.name} not available due to missing dependencies")
        
        return available
    
    def get_all_modules(self) -> Dict[str, AnalysisModule]:
        """
        Get all registered modules regardless of availability
        
        Returns:
            Dictionary mapping module names to all module instances
        """
        return self._modules.copy()
    
    def get_modules_by_category(self, category: str) -> Dict[str, AnalysisModule]:
        """
        Get modules filtered by category
        
        Args:
            category: Category name (e.g., 'annotation', 'trajectory')
            
        Returns:
            Dictionary of modules in the specified category
        """
        category_modules = {}
        for name, module in self._modules.items():
            # Check if module name or description contains category
            if (category.lower() in name.lower() or 
                category.lower() in module.description.lower()):
                category_modules[name] = module
        
        return category_modules
    
    def get_module_info(self, name: str) -> Optional[Dict]:
        """
        Get detailed information about a module
        
        Args:
            name: Module name
            
        Returns:
            Dictionary with module information or None if not found
        """
        module = self.get_module(name)
        if not module:
            return None
        
        # Check dependencies
        dep_status = self.dependency_checker.check_module_dependencies(
            module.required_dependencies,
            module.optional_dependencies
        )
        
        return {
            'name': module.name,
            'description': module.description,
            'version': module.version,
            'available': module.is_available(),
            'required_dependencies': module.required_dependencies,
            'optional_dependencies': module.optional_dependencies,
            'available_methods': module.get_available_methods() if module.is_available() else [],
            'dependency_status': dep_status,
            'visualization_options': module.get_visualization_options()
        }
    
    def list_modules(self, available_only: bool = False) -> List[str]:
        """
        List all module names
        
        Args:
            available_only: If True, only return available modules
            
        Returns:
            List of module names
        """
        if available_only:
            return list(self.get_available_modules().keys())
        else:
            return list(self._modules.keys())
    
    def diagnose_all_modules(self) -> str:
        """
        Generate diagnostic report for all modules
        
        Returns:
            Human-readable diagnostic report
        """
        lines = ["SingleCellStudio Module Diagnostic Report", "=" * 50]
        
        if not self._modules:
            lines.append("No modules found!")
            return '\n'.join(lines)
        
        available_count = len(self.get_available_modules())
        total_count = len(self._modules)
        
        lines.append(f"Total modules: {total_count}")
        lines.append(f"Available modules: {available_count}")
        lines.append(f"Unavailable modules: {total_count - available_count}")
        lines.append("")
        
        # List each module
        for name, module in self._modules.items():
            lines.append(f"Module: {module.name}")
            lines.append(f"  Status: {'✅ Available' if module.is_available() else '❌ Unavailable'}")
            lines.append(f"  Description: {module.description}")
            lines.append(f"  Version: {module.version}")
            
            if not module.is_available():
                dep_status = self.dependency_checker.check_module_dependencies(
                    module.required_dependencies,
                    module.optional_dependencies
                )
                if dep_status['missing_required']:
                    lines.append(f"  Missing required: {', '.join(dep_status['missing_required'])}")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def reload_modules(self):
        """Reload all modules (useful for development)"""
        self._modules.clear()
        self._module_classes.clear()
        self.dependency_checker.clear_cache()
        self._load_modules()
        logger.info("All modules reloaded")
    
    def get_system_report(self) -> Dict:
        """
        Get comprehensive system and module report
        
        Returns:
            Dictionary with system-wide information
        """
        system_report = self.dependency_checker.get_system_report()
        
        # Add module-specific information
        system_report['modules'] = {
            'total_count': len(self._modules),
            'available_count': len(self.get_available_modules()),
            'modules': {name: self.get_module_info(name) for name in self._modules.keys()}
        }
        
        return system_report 