"""
Comprehensive dependency checker for SingleCellStudio modules
"""

from typing import Dict, List, Tuple, Set
import logging
from .optional_imports import check_package_availability, get_package_version, OPTIONAL_PACKAGES

logger = logging.getLogger("SingleCellStudio.DependencyChecker")

class DependencyChecker:
    """
    Comprehensive dependency checking and reporting
    """
    
    def __init__(self):
        self._cache = {}  # Cache results to avoid repeated checks
        
    def check_module_dependencies(self, required: List[str], 
                                 optional: List[str] = None) -> Dict[str, any]:
        """
        Check dependencies for a specific module
        
        Args:
            required: List of required package names
            optional: List of optional package names
            
        Returns:
            Dictionary with dependency status and details
        """
        optional = optional or []
        
        # Create cache key
        cache_key = tuple(sorted(required + optional))
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = {
            'available': True,
            'required_status': {},
            'optional_status': {},
            'missing_required': [],
            'available_optional': [],
            'missing_optional': [],
            'error_message': None
        }
        
        # Check required dependencies
        if required:
            required_status = check_package_availability(required)
            result['required_status'] = required_status
            
            missing_required = [pkg for pkg, available in required_status.items() if not available]
            result['missing_required'] = missing_required
            
            if missing_required:
                result['available'] = False
                result['error_message'] = f"Missing required packages: {', '.join(missing_required)}"
        
        # Check optional dependencies
        if optional:
            optional_status = check_package_availability(optional)
            result['optional_status'] = optional_status
            
            result['available_optional'] = [pkg for pkg, available in optional_status.items() if available]
            result['missing_optional'] = [pkg for pkg, available in optional_status.items() if not available]
        
        # Cache result
        self._cache[cache_key] = result
        return result
    
    def get_system_report(self) -> Dict[str, any]:
        """
        Generate comprehensive system dependency report
        
        Returns:
            Dictionary with system-wide dependency information
        """
        report = {
            'core_dependencies': {},
            'optional_categories': {},
            'recommendations': [],
            'warnings': []
        }
        
        # Check core dependencies
        core_packages = ['scanpy', 'anndata', 'pandas', 'numpy', 'matplotlib', 'seaborn']
        core_status = check_package_availability(core_packages)
        
        for pkg, available in core_status.items():
            if available:
                version = get_package_version(pkg)
                report['core_dependencies'][pkg] = {
                    'available': True,
                    'version': version
                }
            else:
                report['core_dependencies'][pkg] = {
                    'available': False,
                    'version': None
                }
                report['warnings'].append(f"Core package {pkg} is not available")
        
        # Check optional categories
        for category, packages in OPTIONAL_PACKAGES.items():
            category_status = check_package_availability(packages)
            available_count = sum(1 for available in category_status.values() if available)
            
            report['optional_categories'][category] = {
                'packages': category_status,
                'available_count': available_count,
                'total_count': len(packages),
                'coverage': available_count / len(packages) if packages else 0
            }
            
            # Add recommendations based on coverage
            coverage = available_count / len(packages) if packages else 0
            if coverage == 0:
                report['recommendations'].append(
                    f"Consider installing packages for {category} analysis: {', '.join(packages[:2])}"
                )
            elif coverage < 0.5:
                missing = [pkg for pkg, avail in category_status.items() if not avail]
                report['recommendations'].append(
                    f"Enhance {category} capabilities by installing: {', '.join(missing[:2])}"
                )
        
        return report
    
    def get_installation_commands(self, missing_packages: List[str]) -> Dict[str, str]:
        """
        Generate installation commands for missing packages
        
        Args:
            missing_packages: List of package names to install
            
        Returns:
            Dictionary with different installation methods
        """
        if not missing_packages:
            return {}
        
        # Create installation commands
        pip_packages = []
        conda_packages = []
        special_instructions = {}
        
        # Package-specific installation mappings
        conda_available = {
            'scanpy', 'anndata', 'pandas', 'numpy', 'matplotlib', 'seaborn',
            'umap-learn', 'leidenalg', 'python-igraph', 'plotly', 'bokeh'
        }
        
        special_cases = {
            'celltypist': 'pip install celltypist',
            'scvelo': 'pip install scvelo',
            'cellrank': 'pip install cellrank',
            'squidpy': 'pip install squidpy',
        }
        
        for package in missing_packages:
            base_package = package.split('.')[0]  # Handle package.module format
            
            if base_package in special_cases:
                special_instructions[package] = special_cases[base_package]
            elif base_package in conda_available:
                conda_packages.append(base_package)
            else:
                pip_packages.append(base_package)
        
        commands = {}
        
        if conda_packages:
            commands['conda'] = f"conda install -c conda-forge {' '.join(conda_packages)}"
        
        if pip_packages:
            commands['pip'] = f"pip install {' '.join(pip_packages)}"
        
        if special_instructions:
            commands['special'] = special_instructions
        
        return commands
    
    def clear_cache(self):
        """Clear the dependency check cache"""
        self._cache.clear()
        logger.debug("Dependency check cache cleared")
    
    def diagnose_module(self, module) -> str:
        """
        Generate diagnostic information for a specific module
        
        Args:
            module: AnalysisModule instance
            
        Returns:
            Human-readable diagnostic string
        """
        try:
            # Check if module follows the interface
            if not hasattr(module, 'required_dependencies'):
                return f"Module {module.__class__.__name__} missing required_dependencies property"
            
            if not hasattr(module, 'optional_dependencies'):
                return f"Module {module.__class__.__name__} missing optional_dependencies property"
            
            # Check dependencies
            dep_status = self.check_module_dependencies(
                module.required_dependencies,
                module.optional_dependencies
            )
            
            lines = [f"Module: {module.name}"]
            lines.append(f"Available: {'✅' if dep_status['available'] else '❌'}")
            
            if dep_status['missing_required']:
                lines.append(f"Missing required: {', '.join(dep_status['missing_required'])}")
            
            if dep_status['available_optional']:
                lines.append(f"Available optional: {', '.join(dep_status['available_optional'])}")
            
            if dep_status['missing_optional']:
                lines.append(f"Missing optional: {', '.join(dep_status['missing_optional'])}")
            
            # Add installation suggestions
            if dep_status['missing_required']:
                install_cmds = self.get_installation_commands(dep_status['missing_required'])
                if install_cmds:
                    lines.append("Installation suggestions:")
                    for method, cmd in install_cmds.items():
                        if method != 'special':
                            lines.append(f"  {method}: {cmd}")
            
            return '\n'.join(lines)
            
        except Exception as e:
            return f"Error diagnosing module {module.__class__.__name__}: {e}" 