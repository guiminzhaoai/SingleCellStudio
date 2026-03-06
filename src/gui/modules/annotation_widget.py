"""
GUI widget for cell annotation module
"""

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                               QDoubleSpinBox, QGroupBox, QPushButton, QTextEdit, QCheckBox)
from PySide6.QtCore import Qt
import logging

from .base_module_widget import BaseModuleWidget

logger = logging.getLogger("SingleCellStudio.AnnotationWidget")

class AnnotationWidget(BaseModuleWidget):
    """Specialized widget for cell annotation module"""
    
    def __init__(self, module, parent=None):
        self.method_combo = None
        self.confidence_spinbox = None
        self.custom_markers_text = None
        self.use_custom_markers_check = None
        self.visualize_button = None
        super().__init__(module, parent)
    
    def setup_ui(self):
        """Set up the user interface with annotation-specific controls"""
        # Call parent setup first
        super().setup_ui()
        
        # Get the main layout
        layout = self.layout()
        
        # Insert parameters section before the controls
        params_group = QGroupBox("Parameters")
        params_layout = QVBoxLayout(params_group)
        
        # Method selection
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Annotation Method:"))
        
        self.method_combo = QComboBox()
        if self.module.is_available():
            methods = self.module.get_available_methods()
            self.method_combo.addItems(methods)
        else:
            self.method_combo.addItems(['auto', 'marker_based', 'reference_based'])
        self.method_combo.setCurrentText('auto')
        method_layout.addWidget(self.method_combo)
        
        params_layout.addLayout(method_layout)
        
        # Confidence threshold
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(QLabel("Confidence Threshold:"))
        
        self.confidence_spinbox = QDoubleSpinBox()
        self.confidence_spinbox.setRange(0.0, 1.0)
        self.confidence_spinbox.setValue(0.5)
        self.confidence_spinbox.setSingleStep(0.1)
        self.confidence_spinbox.setDecimals(2)
        confidence_layout.addWidget(self.confidence_spinbox)
        
        params_layout.addLayout(confidence_layout)
        
        # Custom markers section
        self.use_custom_markers_check = QCheckBox("Use Custom Marker Genes")
        self.use_custom_markers_check.stateChanged.connect(self.on_custom_markers_toggled)
        params_layout.addWidget(self.use_custom_markers_check)
        
        # Custom markers text area
        custom_markers_label = QLabel("Custom Markers (JSON format):")
        params_layout.addWidget(custom_markers_label)
        
        self.custom_markers_text = QTextEdit()
        self.custom_markers_text.setMaximumHeight(100)
        self.custom_markers_text.setEnabled(False)
        self.custom_markers_text.setPlainText('''{
    "T cells": ["CD3D", "CD3E", "CD3G"],
    "B cells": ["CD19", "MS4A1", "CD79A"],
    "NK cells": ["GNLY", "NKG7", "KLRD1"],
    "Monocytes": ["CD14", "LYZ", "S100A9"]
}''')
        params_layout.addWidget(self.custom_markers_text)
        
        # Insert parameters group before controls (index 2, after header and status)
        layout.insertWidget(2, params_group)
        
        # Add visualization button to results section
        # Find the results group by iterating through widgets
        results_group = None
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, QGroupBox) and widget.title() == "Results":
                results_group = widget
                break
        
        if results_group:
            results_layout = results_group.layout()
            
            self.visualize_button = QPushButton("Create Visualization")
            self.visualize_button.setEnabled(False)
            results_layout.addWidget(self.visualize_button)
            
            self.visualize_button.clicked.connect(self.create_visualization)
        else:
            # Fallback: create visualization button separately
            self.visualize_button = QPushButton("Create Visualization")
            self.visualize_button.setEnabled(False)
            layout.addWidget(self.visualize_button)
            self.visualize_button.clicked.connect(self.create_visualization)
    
    def run_analysis(self):
        """Run analysis with annotation-specific parameters"""
        logger.info("Starting run_analysis")
        
        if self.adata is None:
            self.progress_label.setText("No data available")
            logger.warning("No data available for annotation")
            return
        
        if not self.module.is_available():
            self.progress_label.setText("Module not available")
            logger.warning("Module not available for annotation")
            return
        
        try:
            logger.info("Setting up UI for analysis")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(25)
            self.progress_label.setText("Starting annotation analysis...")
            if self.run_button:
                self.run_button.setEnabled(False)
            
            # Get parameters from widgets
            method = self.method_combo.currentText()
            confidence_threshold = self.confidence_spinbox.value()
            
            # Get custom markers if enabled
            custom_markers = ""
            if self.use_custom_markers_check.isChecked() and method == 'marker_based':
                custom_markers = self.custom_markers_text.toPlainText().strip()
            
            self.progress_bar.setValue(50)
            self.progress_label.setText(f"Running {method} annotation...")
            
            # Run analysis with parameters
            results = self.module.run_analysis(
                self.adata, 
                method=method,
                confidence_threshold=confidence_threshold,
                custom_markers=custom_markers
            )
            
            if results.get('success', False):
                self.progress_bar.setValue(100)
                self.progress_label.setText("Cell annotation completed!")
                self.display_results(results)
                self.results = results
                if self.visualize_button:
                    self.visualize_button.setEnabled(True)
                self.analysis_completed.emit(results)
            else:
                error_msg = results.get('error', 'Annotation failed')
                self.progress_label.setText(f"Annotation failed: {error_msg}")
                self.analysis_failed.emit(error_msg)
            
        except Exception as e:
            error_msg = str(e)
            self.progress_label.setText(f"Error: {error_msg}")
            self.analysis_failed.emit(error_msg)
        
        finally:
            self.progress_bar.setVisible(False)
            if self.run_button:
                self.run_button.setEnabled(True)
    
    def display_results(self, results):
        """Display annotation-specific results"""
        text_lines = [f"Cell Annotation Results"]
        text_lines.append("=" * 30)
        text_lines.append(f"Method used: {results.get('method_used', 'Unknown')}")
        text_lines.append("")
        
        # Add annotation-specific information
        summary = results.get('summary', {})
        if summary:
            text_lines.append("Summary:")
            text_lines.append(f"  Total cells: {summary.get('total_cells', 'N/A')}")
            text_lines.append(f"  Unique cell types: {summary.get('unique_cell_types', 'N/A')}")
            text_lines.append(f"  Mean confidence: {summary.get('mean_confidence', 0):.3f}")
            text_lines.append(f"  High confidence cells: {summary.get('high_confidence_cells', 'N/A')}")
            
            # Show cell type counts
            cell_type_counts = summary.get('cell_type_counts', {})
            if cell_type_counts:
                text_lines.append("")
                text_lines.append("Cell type distribution:")
                for cell_type, count in cell_type_counts.items():
                    percentage = (count / summary.get('total_cells', 1)) * 100
                    text_lines.append(f"  {cell_type}: {count} cells ({percentage:.1f}%)")
        
        # Add method details if available
        method_details = results.get('method_details', {})
        if method_details:
            text_lines.append("")
            text_lines.append("Method details:")
            for key, value in method_details.items():
                if key != 'cluster_mapping':  # Skip large data structures
                    text_lines.append(f"  {key}: {value}")
        
        self.results_text.setPlainText("\n".join(text_lines))
    
    def create_visualization(self):
        """Create visualization for annotation results"""
        if not self.results or not self.adata:
            self.progress_label.setText("No results available for visualization")
            return
        
        try:
            self.progress_label.setText("Creating visualization...")
            
            # Get available visualization options
            viz_options = self.module.get_visualization_options()
            if not viz_options:
                self.progress_label.setText("No visualization options available")
                return
            
            # Create UMAP visualization if available
            if 'umap_celltype' in viz_options and 'X_umap' in self.adata.obsm:
                plot_type = 'umap_celltype'
            else:
                plot_type = viz_options[0]  # Use first available option
            
            # Create visualization
            fig = self.module.create_visualization(
                self.adata, 
                self.results, 
                plot_type=plot_type
            )
            
            if fig:
                # Show the plot
                import matplotlib.pyplot as plt
                plt.show()
                self.progress_label.setText(f"Created {plot_type} visualization")
            else:
                self.progress_label.setText("Failed to create visualization")
                
        except Exception as e:
            logger.error(f"Visualization error: {e}")
            self.progress_label.setText(f"Visualization error: {str(e)}")
    
    def on_custom_markers_toggled(self, state):
        """Handle custom markers checkbox toggle"""
        self.custom_markers_text.setEnabled(state == 2)  # 2 = checked
        if state == 2:
            self.progress_label.setText("Custom markers enabled. Edit the JSON above.")
        else:
            self.progress_label.setText("Using default marker genes.")
    
    def set_data(self, adata):
        """Set data and update UI accordingly"""
        logger.info(f"Setting data: {adata is not None}")
        super().set_data(adata)
        
        # Update method options based on data and availability
        if adata is not None and self.module.is_available():
            logger.info("Data is available and module is available")
            # Check if clustering results exist
            if 'leiden' in adata.obs.columns:
                self.progress_label.setText("Data loaded. Clustering results found. Ready for annotation.")
            else:
                self.progress_label.setText("Data loaded but no clustering results found. Please run clustering first.")
                if self.run_button:
                    self.run_button.setEnabled(False)
            
            # Update available methods
            methods = self.module.get_available_methods()
            current_text = self.method_combo.currentText()
            self.method_combo.clear()
            self.method_combo.addItems(methods)
            
            # Restore selection if still available
            if current_text in methods:
                self.method_combo.setCurrentText(current_text)
            else:
                self.method_combo.setCurrentText('auto') 