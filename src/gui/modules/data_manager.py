"""
Data Manager for Modular Architecture

This module provides a centralized data management system that allows
modules to share data while maintaining their independence.
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
import pandas as pd
from PySide6.QtCore import QObject, Signal

class DataManager(QObject):
    """Central data manager for sharing data between modules"""
    
    # Signals for data updates
    data_updated = Signal(str, object)  # (data_key, data_value)
    annotation_updated = Signal(object)  # Updated annotation data
    analysis_results_updated = Signal(str, object)  # (analysis_name, results)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Core data storage
        self._data_store: Dict[str, Any] = {}
        
        # Specific data types for common use cases
        self._main_adata = None  # Main AnnData object
        self._annotation_results = {}  # Cell annotation results
        self._analysis_results = {}  # Analysis results from various modules
        self._metadata = {}  # Additional metadata
        
        # Data change listeners
        self._listeners: Dict[str, List[Callable]] = {}
        
        self.logger.info("Data manager initialized")
    
    def set_main_data(self, adata, source_module: str = "unknown"):
        """Set the main AnnData object"""
        self._main_adata = adata
        self._data_store['main_adata'] = adata
        
        self.logger.info(f"Main data updated by {source_module}: {adata.n_obs} cells × {adata.n_vars} genes")
        
        # Notify all listeners
        self.data_updated.emit('main_adata', adata)
        self._notify_listeners('main_adata', adata)
    
    def get_main_data(self):
        """Get the main AnnData object"""
        return self._main_adata
    
    def set_annotation_results(self, results: Dict[str, Any], source_module: str = "annotation"):
        """Set cell annotation results"""
        self._annotation_results.update(results)
        self._data_store['annotation_results'] = self._annotation_results
        
        self.logger.info(f"Annotation results updated by {source_module}")
        
        # Add annotation to main data if available
        if self._main_adata is not None and 'cell_types' in results:
            self._main_adata.obs['cell_type'] = results['cell_types']
            self._main_adata.obs['annotation_confidence'] = results.get('confidence', 1.0)
        
        # Notify listeners
        self.annotation_updated.emit(self._annotation_results)
        self._notify_listeners('annotation_results', self._annotation_results)
    
    def get_annotation_results(self) -> Dict[str, Any]:
        """Get cell annotation results"""
        return self._annotation_results.copy()
    
    def set_analysis_results(self, analysis_name: str, results: Dict[str, Any], source_module: str = "unknown"):
        """Set results from any analysis module"""
        self._analysis_results[analysis_name] = results
        self._data_store[f'analysis_{analysis_name}'] = results
        
        self.logger.info(f"Analysis results '{analysis_name}' updated by {source_module}")
        
        # Notify listeners
        self.analysis_results_updated.emit(analysis_name, results)
        self._notify_listeners(f'analysis_{analysis_name}', results)
    
    def get_analysis_results(self, analysis_name: str = None) -> Dict[str, Any]:
        """Get analysis results"""
        if analysis_name:
            return self._analysis_results.get(analysis_name, {})
        return self._analysis_results.copy()
    
    def set_data(self, key: str, value: Any, source_module: str = "unknown"):
        """Set arbitrary data"""
        self._data_store[key] = value
        self.logger.debug(f"Data '{key}' set by {source_module}")
        
        # Notify listeners
        self.data_updated.emit(key, value)
        self._notify_listeners(key, value)
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get arbitrary data"""
        return self._data_store.get(key, default)
    
    def has_data(self, key: str) -> bool:
        """Check if data exists"""
        return key in self._data_store
    
    def list_data_keys(self) -> List[str]:
        """List all available data keys"""
        return list(self._data_store.keys())
    
    def add_listener(self, key: str, callback: Callable):
        """Add a callback for data changes"""
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)
        self.logger.debug(f"Added listener for '{key}'")
    
    def remove_listener(self, key: str, callback: Callable):
        """Remove a callback for data changes"""
        if key in self._listeners and callback in self._listeners[key]:
            self._listeners[key].remove(callback)
            self.logger.debug(f"Removed listener for '{key}'")
    
    def _notify_listeners(self, key: str, value: Any):
        """Notify all listeners for a specific key"""
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(value)
                except Exception as e:
                    self.logger.error(f"Error in listener callback for '{key}': {e}")
    
    def get_data_summary(self) -> Dict[str, str]:
        """Get a summary of all stored data"""
        summary = {}
        
        if self._main_adata is not None:
            summary['main_data'] = f"{self._main_adata.n_obs} cells × {self._main_adata.n_vars} genes"
        
        if self._annotation_results:
            n_annotated = len(self._annotation_results.get('cell_types', []))
            summary['annotations'] = f"{n_annotated} cells annotated"
        
        if self._analysis_results:
            summary['analyses'] = f"{len(self._analysis_results)} analysis results"
        
        summary['total_data_items'] = str(len(self._data_store))
        
        return summary
    
    def clear_data(self, key: str = None):
        """Clear specific data or all data"""
        if key:
            if key in self._data_store:
                del self._data_store[key]
                self.logger.info(f"Cleared data: {key}")
        else:
            self._data_store.clear()
            self._main_adata = None
            self._annotation_results.clear()
            self._analysis_results.clear()
            self._metadata.clear()
            self.logger.info("Cleared all data")
    
    def export_data(self, output_path: Path, data_keys: List[str] = None):
        """Export data to files"""
        if data_keys is None:
            data_keys = list(self._data_store.keys())
        
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported = []
        
        # Export main data
        if 'main_adata' in data_keys and self._main_adata is not None:
            adata_path = output_path / "main_data.h5ad"
            self._main_adata.write(adata_path)
            exported.append(f"main_data.h5ad")
        
        # Export annotation results
        if 'annotation_results' in data_keys and self._annotation_results:
            anno_path = output_path / "annotation_results.json"
            import json
            with open(anno_path, 'w') as f:
                # Convert non-serializable objects to strings
                serializable_results = {}
                for k, v in self._annotation_results.items():
                    if isinstance(v, (list, dict, str, int, float, bool)):
                        serializable_results[k] = v
                    else:
                        serializable_results[k] = str(v)
                json.dump(serializable_results, f, indent=2)
            exported.append("annotation_results.json")
        
        # Export analysis results
        if self._analysis_results:
            for analysis_name, results in self._analysis_results.items():
                if f'analysis_{analysis_name}' in data_keys:
                    result_path = output_path / f"analysis_{analysis_name}.json"
                    import json
                    with open(result_path, 'w') as f:
                        # Convert non-serializable objects to strings
                        serializable_results = {}
                        for k, v in results.items():
                            if isinstance(v, (list, dict, str, int, float, bool)):
                                serializable_results[k] = v
                            else:
                                serializable_results[k] = str(v)
                        json.dump(serializable_results, f, indent=2)
                    exported.append(f"analysis_{analysis_name}.json")
        
        self.logger.info(f"Exported {len(exported)} data files to {output_path}")
        return exported

# Global data manager instance
data_manager = DataManager() 