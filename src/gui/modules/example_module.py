"""
Example GUI Module

This is an example of how to create a modular GUI component
that can be registered with the module system.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QGroupBox, QSpinBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.gui.modules.module_registry import BaseGUIModule

class ExampleModule(BaseGUIModule):
    """Example module demonstrating the modular architecture"""
    
    # Signals for communication with main window
    analysis_requested = Signal(dict)  # Emit analysis parameters
    data_updated = Signal(object)     # Emit updated data
    
    @property 
    def module_name(self) -> str:
        return "example_module"
    
    @property
    def display_name(self) -> str:
        return "Example Analysis"
    
    @property
    def description(self) -> str:
        return "Example module showing how to integrate custom analysis tools"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def requirements(self) -> list:
        return ["numpy", "pandas"]  # Required dependencies
    
    def create_widget(self, parent=None):
        """Create the main widget for this module"""
        if self._widget is not None:
            return self._widget
        
        self._widget = QWidget(parent)
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Example Analysis Module")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #2c3e50; padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        layout.addWidget(header)
        
        # Control panel
        control_group = QGroupBox("Analysis Controls")
        control_layout = QVBoxLayout()
        
        # Parameters
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("Parameter 1:"))
        self.param1_spin = QSpinBox()
        self.param1_spin.setRange(1, 100)
        self.param1_spin.setValue(10)
        params_layout.addWidget(self.param1_spin)
        control_layout.addLayout(params_layout)
        
        # Run button
        self.run_btn = QPushButton("Run Example Analysis")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.run_btn.clicked.connect(self.run_analysis)
        control_layout.addWidget(self.run_btn)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Results panel
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setText("No analysis run yet...")
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Data info
        self.data_info = QLabel("No data loaded")
        self.data_info.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 5px;")
        layout.addWidget(self.data_info)
        
        layout.addStretch()
        self._widget.setLayout(layout)
        
        return self._widget
    
    def initialize(self):
        """Initialize the module"""
        self.logger.info("Example module initialized")
        self.current_data = None
    
    def set_data(self, adata):
        """Set analysis data for the module"""
        self.current_data = adata
        if adata is not None:
            info_text = f"Data loaded: {adata.n_obs:,} cells × {adata.n_vars:,} genes"
            self.data_info.setText(info_text)
            self.run_btn.setEnabled(True)
        else:
            self.data_info.setText("No data loaded")
            self.run_btn.setEnabled(False)
    
    def run_analysis(self):
        """Run the example analysis"""
        if self.current_data is None:
            QMessageBox.warning(
                self._widget, 
                "No Data", 
                "Please load data before running analysis."
            )
            return
        
        try:
            # Get parameters
            param1 = self.param1_spin.value()
            
            # Simulate analysis
            import time
            self.results_text.setText("Running analysis...")
            self._widget.repaint()  # Force UI update
            
            # Simulate some processing time
            time.sleep(1)
            
            # Mock results
            results = f"""Example Analysis Results:
            
Parameter 1: {param1}
Cells analyzed: {self.current_data.n_obs:,}
Genes analyzed: {self.current_data.n_vars:,}

Mock Analysis Results:
• Processing completed successfully
• Parameter 1 had value: {param1}
• Analysis type: Example computation
• Status: ✅ Complete

This is a demonstration of how modules can:
1. Accept parameters from UI
2. Process data independently  
3. Display results in their own interface
4. Communicate with the main window through signals
"""
            
            self.results_text.setText(results)
            
            # Emit signal to notify main window
            analysis_params = {"param1": param1, "module": self.module_name}
            self.analysis_requested.emit(analysis_params)
            
            self.logger.info(f"Example analysis completed with param1={param1}")
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            self.results_text.setText(error_msg)
            self.logger.error(error_msg)
    
    def get_menu_actions(self):
        """Return menu actions for this module"""
        return [
            {
                "text": "Run Example Analysis",
                "callback": self.run_analysis,
                "shortcut": "Ctrl+E"
            },
            {
                "text": "Clear Example Results", 
                "callback": self.clear_results
            }
        ]
    
    def clear_results(self):
        """Clear analysis results"""
        self.results_text.setText("Results cleared...")
        self.logger.info("Example module results cleared")
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Example module cleaned up")
        self.current_data = None 