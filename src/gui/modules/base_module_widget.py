"""
Base widget class for analysis module GUIs
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTextEdit, QGroupBox, QProgressBar)
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any
import logging

logger = logging.getLogger("SingleCellStudio.BaseModuleWidget")

class BaseModuleWidget(QWidget):
    """Base widget class for all analysis module GUIs"""
    
    analysis_completed = Signal(dict)
    analysis_failed = Signal(str)
    
    def __init__(self, module, parent=None):
        super().__init__(parent)
        self.module = module
        self.adata = None
        self.results = None
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Module header
        header_group = QGroupBox(self.module.name)
        header_layout = QVBoxLayout(header_group)
        
        desc_label = QLabel(self.module.description)
        desc_label.setWordWrap(True)
        header_layout.addWidget(desc_label)
        
        layout.addWidget(header_group)
        
        # Status
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        
        availability_text = "✅ Available" if self.module.is_available() else "❌ Unavailable"
        self.status_label = QLabel(availability_text)
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
        
        # Controls
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setEnabled(self.module.is_available())
        controls_layout.addWidget(self.run_button)
        
        layout.addWidget(controls_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready to run analysis")
        layout.addWidget(self.progress_label)
        
        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setPlainText("No results yet.")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
    
    def setup_connections(self):
        """Set up signal connections"""
        self.run_button.clicked.connect(self.run_analysis)
    
    def set_data(self, adata):
        """Set the data for analysis"""
        self.adata = adata
        if adata is not None:
            is_valid, error_msg = self.module.validate_data(adata)
            if is_valid:
                self.progress_label.setText("Data loaded successfully.")
                self.run_button.setEnabled(self.module.is_available())
            else:
                self.progress_label.setText(f"Data validation failed: {error_msg}")
                self.run_button.setEnabled(False)
        else:
            self.progress_label.setText("No data loaded.")
            self.run_button.setEnabled(False)
    
    def run_analysis(self):
        """Run analysis"""
        if self.adata is None:
            self.progress_label.setText("No data available")
            return
        
        if not self.module.is_available():
            self.progress_label.setText("Module not available")
            return
        
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(50)
            self.progress_label.setText("Running analysis...")
            self.run_button.setEnabled(False)
            
            # Run analysis
            results = self.module.run_analysis(self.adata)
            
            if results.get('success', False):
                self.progress_bar.setValue(100)
                self.progress_label.setText("Analysis completed!")
                self.display_results(results)
                self.results = results
                self.analysis_completed.emit(results)
            else:
                error_msg = results.get('error', 'Analysis failed')
                self.progress_label.setText(f"Analysis failed: {error_msg}")
                self.analysis_failed.emit(error_msg)
            
        except Exception as e:
            error_msg = str(e)
            self.progress_label.setText(f"Error: {error_msg}")
            self.analysis_failed.emit(error_msg)
        
        finally:
            self.progress_bar.setVisible(False)
            self.run_button.setEnabled(True)
    
    def display_results(self, results):
        """Display analysis results"""
        text_lines = [f"Analysis completed using {self.module.name}"]
        text_lines.append(f"Method: {results.get('method_used', 'Unknown')}")
        text_lines.append("")
        
        summary = results.get('summary', {})
        if summary:
            text_lines.append("Summary:")
            for key, value in summary.items():
                text_lines.append(f"  {key}: {value}")
        
        self.results_text.setPlainText("\n".join(text_lines)) 