"""
Simple Cell-Cell Interaction Analysis Module

This is a simplified version to test module loading without complex dependencies.
"""

import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.gui.modules.module_registry import BaseGUIModule

class SimpleCellInteractionModule(BaseGUIModule):
    """Simple Cell-Cell Interaction Analysis Module"""
    
    # Signals for communication with main window
    analysis_requested = Signal(dict)
    results_ready = Signal(dict)
    
    def __init__(self, parent=None):
        """Initialize the module"""
        super().__init__(parent)
        self.current_data = None
    
    @property
    def module_name(self) -> str:
        return "simple_cell_interaction"
    
    @property
    def display_name(self) -> str:
        return "Cell-Cell Interaction (Simple)"
    
    @property
    def description(self) -> str:
        return "Simplified cell-cell interaction analysis module for testing"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def requirements(self) -> list:
        return []  # No special requirements for testing
    
    def create_widget(self, parent=None):
        """Create the main widget for this module"""
        if self._widget is not None:
            return self._widget
        
        self._widget = QWidget(parent)
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Cell-Cell Interaction Analysis (Simple)")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            color: #2c3e50; 
            padding: 15px; 
            background-color: #ecf0f1; 
            border-radius: 8px;
            margin-bottom: 10px;
        """)
        layout.addWidget(header)
        
        # Data status
        self.data_status = QLabel("📊 No data loaded")
        self.data_status.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        layout.addWidget(self.data_status)
        
        # Simple controls
        self.run_button = QPushButton("🚀 Run Simple Analysis")
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.run_button.clicked.connect(self._run_analysis)
        self.run_button.setEnabled(False)
        layout.addWidget(self.run_button)
        
        # Results display
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setReadOnly(True)
        self.results_text.setText("No analysis results yet...")
        layout.addWidget(self.results_text)
        
        layout.addStretch()
        self._widget.setLayout(layout)
        return self._widget
    
    def initialize(self):
        """Initialize the module"""
        self.logger.info("Simple Cell-Cell Interaction module initialized")
    
    def set_data(self, adata):
        """Set analysis data for the module"""
        self.current_data = adata
        if adata is not None:
            info_text = f"📊 Data loaded: {adata.n_obs:,} cells × {adata.n_vars:,} genes"
            self.data_status.setText(info_text)
            self.run_button.setEnabled(True)
        else:
            self.data_status.setText("📊 No data loaded")
            self.run_button.setEnabled(False)
    
    def _run_analysis(self):
        """Run a simple mock analysis"""
        if self.current_data is None:
            self.results_text.setText("❌ No data available for analysis")
            return
        
        # Simple mock analysis
        results = f"""🔗 Simple Cell-Cell Interaction Analysis Results

Data: {self.current_data.n_obs:,} cells × {self.current_data.n_vars:,} genes

Mock Analysis Results:
• Ligand-receptor pairs detected: 156
• Significant interactions: 42
• Top cell type pairs: T cells ↔ Dendritic cells
• Communication pathways: 15 active

Analysis Type: Simple mock analysis
Status: ✅ Completed successfully

This is a simplified version for testing the modular architecture.
The full version will include CellPhoneDB, Squidpy, and COMMOT analysis.
"""
        
        self.results_text.setText(results)
        self.logger.info("Simple cell interaction analysis completed")
        
        # Emit signal
        self.results_ready.emit({"type": "simple_interaction", "status": "completed"})
    
    def get_menu_actions(self):
        """Return menu actions for this module"""
        return [
            {
                "text": "Run Simple Interaction Analysis",
                "callback": self._run_analysis,
                "shortcut": "Ctrl+Shift+I"
            }
        ]
    
    def cleanup(self):
        """Cleanup resources"""
        pass 