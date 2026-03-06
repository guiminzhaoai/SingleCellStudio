"""
SingleCellStudio Professional Main Window

Professional single-window interface combining data import and analysis functionality
with proper menu bars similar to commercial software like CLC Workbench.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QMessageBox, QMenuBar, QStatusBar,
    QTabWidget, QGroupBox, QGridLayout, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QProgressBar, QScrollArea,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTableWidget,
    QTableWidgetItem, QDialog, QFileDialog, QToolBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QIcon, QKeySequence, QAction

# Matplotlib imports for plot display
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    try:
        # Try PySide6 backend
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        import matplotlib.pyplot as plt
        MATPLOTLIB_AVAILABLE = True
    except ImportError:
        MATPLOTLIB_AVAILABLE = False

# Import required modules
try:
    import anndata as ad
    import pandas as pd
    import numpy as np
    from analysis import run_standard_pipeline
    from visualization.matplotlib_backend import MatplotlibPlotter
    ANALYSIS_AVAILABLE = True
    VISUALIZATION_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False
    VISUALIZATION_AVAILABLE = False

try:
    from .data_import_dialog import DataImportDialog
    from ..data import DataLoader, DataFormat, get_data_info, auto_detect_format
    from ..version import __version__, VERSION_STRING
except ImportError:
    try:
        # Fallback imports
        from data_import_dialog import DataImportDialog
        from data import DataLoader, DataFormat, get_data_info, auto_detect_format
        from version import __version__, VERSION_STRING
    except ImportError:
        DataImportDialog = None
        __version__ = "0.2.0"
        VERSION_STRING = "0.2.0-dev"

# Configure logging
logger = logging.getLogger(__name__)

class AnalysisWorker(QThread):
    """Worker thread for running analysis pipeline"""
    
    progress_updated = Signal(int, str)
    analysis_completed = Signal(object, dict)
    analysis_failed = Signal(str)
    
    def __init__(self, adata, pipeline_params=None, output_dir=None):
        super().__init__()
        self.adata = adata
        self.pipeline_params = pipeline_params or {}
        self.output_dir = output_dir
    
    def run(self):
        """Run the analysis pipeline with progress callback"""
        try:
            self.progress_updated.emit(0, "Starting analysis pipeline...")
            
            if not ANALYSIS_AVAILABLE:
                raise ImportError("Analysis modules not available")
            
            # Define a progress callback function that emits the signal
            def progress_callback(step, total_steps, message):
                progress_percent = int((step / total_steps) * 100)
                self.progress_updated.emit(progress_percent, message)

            # Run the standard pipeline with the callback
            result_adata, results = run_standard_pipeline(
                self.adata, 
                output_dir=self.output_dir,
                progress_callback=progress_callback,
                **self.pipeline_params
            )
            
            self.progress_updated.emit(100, "Analysis completed successfully!")
            self.analysis_completed.emit(result_adata, results)
            
        except Exception as e:
            self.analysis_failed.emit(str(e))

class ProfessionalMainWindow(QMainWindow):
    """Professional single-window interface for SingleCellStudio"""
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Data variables
        self.adata = None
        self.analysis_adata = None
        self.analysis_results = None
        self.worker = None
        self.input_file_path = None
        self.output_dir = None
        
        # UI state
        self.current_mode = "welcome"  # welcome, data_loaded, analysis_running, analysis_complete
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the professional user interface"""
        self.setWindowTitle(f"SingleCellStudio {VERSION_STRING} - Professional Edition")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create central widget with tab interface
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create tab widget for different modes
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        
        # Welcome/Data Import Tab
        self.welcome_tab = self.create_welcome_tab()
        self.tab_widget.addTab(self.welcome_tab, "Home")
        
        # QC & Cluster Tab (merged - initially disabled)
        self.qc_cluster_tab = self.create_analysis_results_tab()
        self.tab_widget.addTab(self.qc_cluster_tab, "QC & Cluster")
        self.tab_widget.setTabEnabled(1, False)
        
        # Cell Annotation Tab (dedicated module - initially disabled)
        self.cell_annotation_tab = self.create_cell_annotation_tab()
        self.tab_widget.addTab(self.cell_annotation_tab, "Cell Annotation")
        self.tab_widget.setTabEnabled(2, False)
        
        main_layout.addWidget(self.tab_widget)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        self.central_widget.setLayout(main_layout)
        
        # Create professional menu bar
        self.create_menu_bar()
        
        # Create status bar (removing redundant toolbar)
        self.create_status_bar()
        
        # Apply professional styling
        self.apply_professional_styling()
    
    def create_welcome_tab(self):
        """Create the welcome/home tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Header section
        header_layout = QVBoxLayout()
        
        # Welcome message with logo space
        welcome_label = QLabel("SingleCellStudio Professional")
        welcome_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("color: #2c3e50; margin: 20px;")
        header_layout.addWidget(welcome_label)
        
        version_label = QLabel(f"Version {VERSION_STRING} - Commercial Grade Single Cell Analysis")
        version_label.setFont(QFont("Arial", 12))
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #7f8c8d; margin-bottom: 30px;")
        header_layout.addWidget(version_label)
        
        layout.addLayout(header_layout)
        
        # Main content area with splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Quick Actions
        left_panel = self.create_quick_actions_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - Status and Recent Files
        right_panel = self.create_status_panel()
        content_splitter.addWidget(right_panel)
        
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 2)
        
        layout.addWidget(content_splitter)
        
        tab.setLayout(layout)
        return tab
    
    def create_quick_actions_panel(self):
        """Create quick actions panel for common tasks"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Getting Started section (replaces redundant "Start Here")
        getting_started_group = QGroupBox("Getting Started")
        getting_started_layout = QVBoxLayout()
        
        self.tutorial_btn = QPushButton("📖 View Tutorials")
        self.tutorial_btn.setStyleSheet("font-size: 14px; padding: 10px; background-color: #17a2b8; color: white;")
        self.tutorial_btn.clicked.connect(self.show_tutorials)
        getting_started_layout.addWidget(self.tutorial_btn)
        
        self.user_guide_btn = QPushButton("📋 User Manual")
        self.user_guide_btn.setStyleSheet("font-size: 14px; padding: 10px; background-color: #6f42c1; color: white;")
        self.user_guide_btn.clicked.connect(self.show_user_manual)
        getting_started_layout.addWidget(self.user_guide_btn)
        
        self.sample_data_btn = QPushButton("💾 Download Sample Data")
        self.sample_data_btn.setStyleSheet("font-size: 14px; padding: 10px; background-color: #fd7e14; color: white;")
        self.sample_data_btn.clicked.connect(self.download_sample_data)
        getting_started_layout.addWidget(self.sample_data_btn)
        
        getting_started_group.setLayout(getting_started_layout)
        layout.addWidget(getting_started_group)

        # Quick Actions Group (streamlined)
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()
        
        # Import Data Button
        import_btn = QPushButton("📁 Import Single Cell Data")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        import_btn.clicked.connect(self.import_data)
        actions_layout.addWidget(import_btn)
        
        # Load Previous Results Button
        load_results_btn = QPushButton("📊 Load Previous Results")
        load_results_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 14px;
                padding: 12px;
                border-radius: 6px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        load_results_btn.clicked.connect(self.load_previous_results)
        actions_layout.addWidget(load_results_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Data Formats Group (more concise)
        formats_group = QGroupBox("Supported Data Formats")
        formats_layout = QVBoxLayout()
        
        formats_text = QTextEdit()
        formats_text.setReadOnly(True)
        formats_text.setMaximumHeight(180)
        formats_text.setText("""✅ 10X Genomics formats:
   • H5 files (.h5) - Recommended
   • MTX folders (matrix.mtx.gz + barcodes + features)

✅ Standard formats:
   • AnnData H5AD files (.h5ad)
   • CSV/TSV expression matrices

✅ Features:
   • Automatic format detection
   • Quality control and validation
   • Professional analysis pipeline""")
        
        formats_layout.addWidget(formats_text)
        formats_group.setLayout(formats_layout)
        layout.addWidget(formats_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_status_panel(self):
        """Create status and information panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # System Status Group
        status_group = QGroupBox("📊 System Status")
        status_layout = QVBoxLayout()
        
        # Current data info
        self.data_info_label = QLabel("No data loaded")
        self.data_info_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.data_info_label.setStyleSheet("color: #34495e; padding: 10px;")
        status_layout.addWidget(self.data_info_label)
        
        # System info
        system_info = QTextEdit()
        system_info.setReadOnly(True)
        system_info.setMaximumHeight(150)
        system_info.setText(f"""System Information:
🖥️  Platform: {sys.platform.capitalize()}
🐍  Python: {sys.version.split()[0]}
📊  Analysis: {'✅ Available' if ANALYSIS_AVAILABLE else '❌ Not Available'}
📈  Visualization: {'✅ Available' if VISUALIZATION_AVAILABLE else '❌ Not Available'}
💾  Version: {VERSION_STRING}""")
        status_layout.addWidget(system_info)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Recent Activity Group
        activity_group = QGroupBox("📝 Recent Activity")
        activity_layout = QVBoxLayout()
        
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(200)
        self.activity_log.setText("Welcome to SingleCellStudio Professional!\nReady to analyze single cell data...")
        activity_layout.addWidget(self.activity_log)
        
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_analysis_results_tab(self):
        """Create the merged analysis and results tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Compact data header
        self.data_header = QLabel("No data loaded")
        self.data_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.data_header.setStyleSheet("color: #2c3e50; padding: 5px; background-color: #ecf0f1; border-radius: 3px;")
        layout.addWidget(self.data_header)
        
        # Create main splitter: Analysis (left) and Results (right)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Analysis controls
        analysis_panel = self.create_analysis_panel()
        main_splitter.addWidget(analysis_panel)
        
        # Right panel - Results display
        results_panel = self.create_results_panel()
        main_splitter.addWidget(results_panel)
        
        # Set proportions: 40% analysis, 60% results
        main_splitter.setStretchFactor(0, 4)
        main_splitter.setStretchFactor(1, 6)
        
        layout.addWidget(main_splitter)
        
        tab.setLayout(layout)
        return tab
    
    def create_analysis_panel(self):
        """Create the analysis control panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Analysis controls section
        controls_group = QGroupBox("QC to Cluster")
        controls_layout = QVBoxLayout()
        
        # Run analysis button
        self.run_analysis_btn = QPushButton("Run QC to Cluster")
        self.run_analysis_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 20px;
                border-radius: 10px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.run_analysis_btn.clicked.connect(self.run_standard_analysis)
        controls_layout.addWidget(self.run_analysis_btn)
        
        # Parameters section
        params_group = QGroupBox("⚙️ Parameters")
        params_layout = QGridLayout()
        
        # Key parameters only
        params_layout.addWidget(QLabel("Min Genes per Cell:"), 0, 0)
        self.min_genes_spin = QSpinBox()
        self.min_genes_spin.setRange(0, 10000)
        self.min_genes_spin.setValue(200)
        params_layout.addWidget(self.min_genes_spin, 0, 1)
        
        params_layout.addWidget(QLabel("Min Cells per Gene:"), 1, 0)
        self.min_cells_spin = QSpinBox()
        self.min_cells_spin.setRange(0, 1000)
        self.min_cells_spin.setValue(3)
        params_layout.addWidget(self.min_cells_spin, 1, 1)
        
        params_layout.addWidget(QLabel("Target Sum:"), 2, 0)
        self.target_sum_spin = QSpinBox()
        self.target_sum_spin.setRange(1000, 100000)
        self.target_sum_spin.setValue(10000)
        params_layout.addWidget(self.target_sum_spin, 2, 1)
        
        params_layout.addWidget(QLabel("N Variable Genes:"), 3, 0)
        self.n_var_genes_spin = QSpinBox()
        self.n_var_genes_spin.setRange(500, 5000)
        self.n_var_genes_spin.setValue(2000)
        params_layout.addWidget(self.n_var_genes_spin, 3, 1)
        
        params_layout.addWidget(QLabel("N PCA Components:"), 4, 0)
        self.n_pca_spin = QSpinBox()
        self.n_pca_spin.setRange(10, 100)
        self.n_pca_spin.setValue(40)
        params_layout.addWidget(self.n_pca_spin, 4, 1)
        
        params_layout.addWidget(QLabel("Clustering Resolution:"), 5, 0)
        self.resolution_spin = QDoubleSpinBox()
        self.resolution_spin.setRange(0.1, 2.0)
        self.resolution_spin.setSingleStep(0.1)
        self.resolution_spin.setValue(0.5)
        params_layout.addWidget(self.resolution_spin, 5, 1)
        
        params_group.setLayout(params_layout)
        controls_layout.addWidget(params_group)
        
        # Progress Log
        progress_group = QGroupBox("Analysis Log")
        progress_layout = QVBoxLayout()
        self.progress_log_display = QTextEdit()
        self.progress_log_display.setReadOnly(True)
        self.progress_log_display.setStyleSheet("font-family: 'Courier New', monospace; font-size: 10pt;")
        self.progress_log_display.setFixedHeight(250)
        progress_layout.addWidget(self.progress_log_display)
        progress_group.setLayout(progress_layout)
        controls_layout.addWidget(progress_group)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_results_panel(self):
        """Create the results display panel, now simplified."""
        panel = QWidget()
        layout = QVBoxLayout()

        # The panel directly contains the standard results components.
        # No need for a sub-tab widget if there's only one view.
        standard_results_widget = self.create_standard_results_tab()
        layout.addWidget(standard_results_widget)
        
        panel.setLayout(layout)
        return panel
    
    def create_standard_results_tab(self):
        """Create the standard analysis results tab"""
        return self.create_results_tab()  # Use existing method
    
    def create_cell_annotation_tab(self):
        """Create dedicated cell annotation tab with advanced visualization"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Data header
        annotation_header = QLabel("Cell Annotation Module")
        annotation_header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        annotation_header.setStyleSheet("color: #2c3e50; padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        layout.addWidget(annotation_header)
        
        # Main splitter: Controls (left) and Visualizations (right)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Annotation controls
        self.create_annotation_controls_panel(main_splitter)
        
        # Right panel - Annotation visualizations
        self.create_annotation_visualization_panel(main_splitter)
        
        # Set proportions: 30% controls, 70% visualizations
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 7)
        
        layout.addWidget(main_splitter)
        
        tab.setLayout(layout)
        return tab
    
    def create_annotation_controls_panel(self, parent_splitter):
        """Create annotation controls panel"""
        try:
            # Import the cell annotation module and widget
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            
            from analysis.modules.annotation.cell_annotation import CellAnnotationModule
            from gui.modules.annotation_widget import AnnotationWidget
            
            # Create the annotation module and widget
            annotation_module = CellAnnotationModule()
            self.annotation_widget = AnnotationWidget(annotation_module)
            
            # Connect signals
            self.annotation_widget.analysis_completed.connect(self.on_annotation_completed)
            self.annotation_widget.analysis_failed.connect(self.on_analysis_failed)
            
            # Add to splitter
            parent_splitter.addWidget(self.annotation_widget)
            
            self.log_activity("Advanced cell annotation module loaded successfully")
            
        except Exception as e:
            self.logger.warning(f"Could not load advanced cell annotation module: {e}")
            
            # Add placeholder panel
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            
            error_label = QLabel("Advanced Cell Annotation Module Unavailable")
            error_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #e74c3c; margin: 20px;")
            placeholder_layout.addWidget(error_label)
            
            reason_label = QLabel(f"Reason: {str(e)}")
            reason_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            reason_label.setStyleSheet("color: #7f8c8d; margin: 10px;")
            placeholder_layout.addWidget(reason_label)
            
            placeholder_layout.addStretch()
            
            parent_splitter.addWidget(placeholder)
            self.annotation_widget = None
            
            self.log_activity(f"Advanced cell annotation module failed to load: {e}")
    
    def create_annotation_visualization_panel(self, parent_splitter):
        """Create advanced annotation visualization panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Visualization tabs
        self.annotation_viz_tabs = QTabWidget()
        
        # UMAP with cell types
        self.create_annotation_umap_tab()
        
        # Cell type proportions
        self.create_annotation_proportions_tab()
        
        # Confidence analysis
        self.create_annotation_confidence_tab()
        
        # Summary statistics
        self.create_annotation_summary_tab()
        
        layout.addWidget(self.annotation_viz_tabs)
        
        panel.setLayout(layout)
        parent_splitter.addWidget(panel)
    
    def create_annotation_umap_tab(self):
        """Create UMAP visualization tab for annotations"""
        if MATPLOTLIB_AVAILABLE:
            umap_widget = QWidget()
            umap_layout = QVBoxLayout()
            
            # Controls
            controls_layout = QHBoxLayout()
            controls_layout.addWidget(QLabel("Color by:"))
            
            self.annotation_color_combo = QComboBox()
            self.annotation_color_combo.addItems(["cell_type", "annotation_confidence", "leiden"])
            controls_layout.addWidget(self.annotation_color_combo)
            
            refresh_btn = QPushButton("Refresh")
            refresh_btn.clicked.connect(self.refresh_annotation_umap)
            controls_layout.addWidget(refresh_btn)
            
            controls_layout.addStretch()
            umap_layout.addLayout(controls_layout)
            
            # Canvas
            self.annotation_umap_canvas = FigureCanvas(Figure(figsize=(10, 8)))
            umap_layout.addWidget(self.annotation_umap_canvas)
            
            umap_widget.setLayout(umap_layout)
            self.annotation_viz_tabs.addTab(umap_widget, "UMAP")
        else:
            placeholder = QLabel("Matplotlib not available")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.annotation_viz_tabs.addTab(placeholder, "UMAP")
    
    def create_annotation_proportions_tab(self):
        """Create cell type proportions tab"""
        if MATPLOTLIB_AVAILABLE:
            prop_widget = QWidget()
            prop_layout = QVBoxLayout()
            
            # Canvas
            self.annotation_prop_canvas = FigureCanvas(Figure(figsize=(10, 8)))
            prop_layout.addWidget(self.annotation_prop_canvas)
            
            prop_widget.setLayout(prop_layout)
            self.annotation_viz_tabs.addTab(prop_widget, "Proportions")
        else:
            placeholder = QLabel("Matplotlib not available")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.annotation_viz_tabs.addTab(placeholder, "Proportions")
    
    def create_annotation_confidence_tab(self):
        """Create confidence analysis tab"""
        if MATPLOTLIB_AVAILABLE:
            conf_widget = QWidget()
            conf_layout = QVBoxLayout()
            
            # Canvas
            self.annotation_conf_canvas = FigureCanvas(Figure(figsize=(10, 8)))
            conf_layout.addWidget(self.annotation_conf_canvas)
            
            conf_widget.setLayout(conf_layout)
            self.annotation_viz_tabs.addTab(conf_widget, "Confidence")
        else:
            placeholder = QLabel("Matplotlib not available")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.annotation_viz_tabs.addTab(placeholder, "Confidence")
    
    def create_annotation_summary_tab(self):
        """Create annotation summary tab"""
        summary_widget = QWidget()
        summary_layout = QVBoxLayout()
        
        # Summary text
        self.annotation_summary_text = QTextEdit()
        self.annotation_summary_text.setReadOnly(True)
        self.annotation_summary_text.setText("No annotation results available")
        self.annotation_summary_text.setStyleSheet("font-family: 'Courier New', monospace; font-size: 11pt;")
        summary_layout.addWidget(self.annotation_summary_text)
        
        summary_widget.setLayout(summary_layout)
        self.annotation_viz_tabs.addTab(summary_widget, "Summary")
    
    def create_analysis_controls(self):
        """Create analysis control panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Pipeline Selection
        pipeline_group = QGroupBox("Analysis Pipeline")
        pipeline_layout = QVBoxLayout()
        
        # Standard pipeline button
        self.run_analysis_btn = QPushButton("Run Standard Single Cell Analysis")
        self.run_analysis_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 20px;
                border-radius: 10px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.run_analysis_btn.clicked.connect(self.run_standard_analysis)
        pipeline_layout.addWidget(self.run_analysis_btn)
        
        # Pipeline steps info
        steps_text = QTextEdit()
        steps_text.setReadOnly(True)
        steps_text.setMaximumHeight(300)
        steps_text.setText("""Standard Pipeline Steps:

1️⃣ Quality Control Metrics
   • Calculate cell/gene QC metrics
   • Identify mitochondrial genes

2️⃣ Cell Filtering
   • Remove low-quality cells
   • Filter by gene count thresholds

3️⃣ Gene Filtering
   • Remove lowly expressed genes
   • Filter by cell expression thresholds

4️⃣ Normalization
   • Log normalization
   • Scale to target sum

5️⃣ Feature Selection
   • Find highly variable genes
   • Select top variable features

6️⃣ Dimensionality Reduction
   • Principal Component Analysis (PCA)
   • UMAP embedding

7️⃣ Clustering
   • Neighborhood graph construction
   • Leiden clustering algorithm

8️⃣ Visualization
   • Generate publication-quality plots
   • Create interactive visualizations""")
        pipeline_layout.addWidget(steps_text)
        
        pipeline_group.setLayout(pipeline_layout)
        layout.addWidget(pipeline_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_analysis_options(self):
        """Create analysis options panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Parameters Group
        params_group = QGroupBox("⚙️ Analysis Parameters")
        params_layout = QGridLayout()
        
        # QC Parameters
        params_layout.addWidget(QLabel("Min Genes per Cell:"), 0, 0)
        self.min_genes_spin = QSpinBox()
        self.min_genes_spin.setRange(0, 10000)
        self.min_genes_spin.setValue(200)
        params_layout.addWidget(self.min_genes_spin, 0, 1)
        
        params_layout.addWidget(QLabel("Min Cells per Gene:"), 1, 0)
        self.min_cells_spin = QSpinBox()
        self.min_cells_spin.setRange(0, 1000)
        self.min_cells_spin.setValue(3)
        params_layout.addWidget(self.min_cells_spin, 1, 1)
        
        # Normalization
        params_layout.addWidget(QLabel("Target Sum:"), 2, 0)
        self.target_sum_spin = QSpinBox()
        self.target_sum_spin.setRange(1000, 100000)
        self.target_sum_spin.setValue(10000)
        params_layout.addWidget(self.target_sum_spin, 2, 1)
        
        # Variable genes
        params_layout.addWidget(QLabel("N Variable Genes:"), 3, 0)
        self.n_var_genes_spin = QSpinBox()
        self.n_var_genes_spin.setRange(500, 5000)
        self.n_var_genes_spin.setValue(2000)
        params_layout.addWidget(self.n_var_genes_spin, 3, 1)
        
        # PCA
        params_layout.addWidget(QLabel("N PCA Components:"), 4, 0)
        self.n_pca_spin = QSpinBox()
        self.n_pca_spin.setRange(10, 100)
        self.n_pca_spin.setValue(40)
        params_layout.addWidget(self.n_pca_spin, 4, 1)
        
        # Clustering
        params_layout.addWidget(QLabel("Clustering Resolution:"), 5, 0)
        self.resolution_spin = QDoubleSpinBox()
        self.resolution_spin.setRange(0.1, 2.0)
        self.resolution_spin.setSingleStep(0.1)
        self.resolution_spin.setValue(0.5)
        params_layout.addWidget(self.resolution_spin, 5, 1)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Output Options
        output_group = QGroupBox("📁 Output Options")
        output_layout = QVBoxLayout()
        
        self.save_intermediate_check = QCheckBox("Save intermediate results")
        self.save_intermediate_check.setChecked(True)
        output_layout.addWidget(self.save_intermediate_check)
        
        self.create_plots_check = QCheckBox("Generate visualization plots")
        self.create_plots_check.setChecked(True)
        output_layout.addWidget(self.create_plots_check)
        
        self.export_metadata_check = QCheckBox("Export metadata tables")
        self.export_metadata_check.setChecked(True)
        output_layout.addWidget(self.export_metadata_check)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_results_tab(self):
        """Create the results tab with plots and analysis results"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Main splitter: Left (plots) and Right (summary + tables)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Visualization plots
        plots_panel = self.create_plots_panel()
        main_splitter.addWidget(plots_panel)
        
        # Right panel - Summary and tables
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Results summary (compact)
        results_summary = self.create_results_summary()
        right_layout.addWidget(results_summary)
        
        # Data tables
        results_tables = self.create_results_tables()
        right_layout.addWidget(results_tables)
        
        right_panel.setLayout(right_layout)
        main_splitter.addWidget(right_panel)
        
        # Set proportions: 60% plots, 40% summary+tables
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 2)
        
        layout.addWidget(main_splitter)
        
        tab.setLayout(layout)
        return tab
    
    def create_plots_panel(self):
        """Create panel to display analysis plots"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Plots header
        plots_header = QLabel("Analysis Visualizations")
        plots_header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        plots_header.setStyleSheet("color: #2c3e50; padding: 8px; background-color: #ecf0f1; border-radius: 4px;")
        layout.addWidget(plots_header)
        
        # Plots tab widget
        self.plots_tabs = QTabWidget()
        
        if MATPLOTLIB_AVAILABLE:
            # Summary plot
            self.summary_plot_widget = QWidget()
            summary_plot_layout = QVBoxLayout()
            self.summary_canvas = FigureCanvas(Figure(figsize=(8, 6)))
            summary_plot_layout.addWidget(self.summary_canvas)
            self.summary_plot_widget.setLayout(summary_plot_layout)
            self.plots_tabs.addTab(self.summary_plot_widget, "Summary")
            
            # UMAP plot
            self.umap_plot_widget = QWidget()
            umap_plot_layout = QVBoxLayout()
            self.umap_canvas = FigureCanvas(Figure(figsize=(8, 6)))
            umap_plot_layout.addWidget(self.umap_canvas)
            self.umap_plot_widget.setLayout(umap_plot_layout)
            self.plots_tabs.addTab(self.umap_plot_widget, "UMAP")
            
            # QC plot
            self.qc_plot_widget = QWidget()
            qc_plot_layout = QVBoxLayout()
            self.qc_canvas = FigureCanvas(Figure(figsize=(8, 6)))
            qc_plot_layout.addWidget(self.qc_canvas)
            self.qc_plot_widget.setLayout(qc_plot_layout)
            self.plots_tabs.addTab(self.qc_plot_widget, "QC Metrics")
            
            # PCA plot
            self.pca_plot_widget = QWidget()
            pca_plot_layout = QVBoxLayout()
            self.pca_canvas = FigureCanvas(Figure(figsize=(8, 6)))
            pca_plot_layout.addWidget(self.pca_canvas)
            self.pca_plot_widget.setLayout(pca_plot_layout)
            self.plots_tabs.addTab(self.pca_plot_widget, "PCA")
            
        else:
            # Fallback if matplotlib not available
            no_plots_label = QLabel("Matplotlib not available for plot display")
            no_plots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.plots_tabs.addTab(no_plots_label, "No Plots")
        
        layout.addWidget(self.plots_tabs)
        panel.setLayout(layout)
        return panel
    
    def create_results_summary(self):
        """Create compact results summary panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Summary stats (more compact)
        summary_group = QGroupBox("Analysis Summary")
        summary_layout = QVBoxLayout()
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setText("No analysis results available")
        self.summary_text.setMaximumHeight(200)  # Limit height
        self.summary_text.setStyleSheet("font-family: 'Courier New', monospace; font-size: 10pt;")
        summary_layout.addWidget(self.summary_text)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Export options (more compact)
        export_group = QGroupBox("Export Results")
        export_layout = QGridLayout()
        
        export_data_btn = QPushButton("Export Data")
        export_data_btn.clicked.connect(self.export_analysis_data)
        export_layout.addWidget(export_data_btn, 0, 0)
        
        export_plots_btn = QPushButton("Export Plots")
        export_plots_btn.clicked.connect(self.export_plots)
        export_layout.addWidget(export_plots_btn, 0, 1)
        
        open_folder_btn = QPushButton("Open Folder")
        open_folder_btn.clicked.connect(self.open_results_folder)
        export_layout.addWidget(open_folder_btn, 1, 0, 1, 2)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_results_tables(self):
        """Create interactive plot generation panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Interactive Plot Generation
        plot_gen_group = QGroupBox("🎨 Interactive Plot Generation")
        plot_gen_layout = QGridLayout()
        
        # Plot type selector
        plot_gen_layout.addWidget(QLabel("Plot Type:"), 0, 0)
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems([
            "UMAP", "PCA", "QC Metrics", "Violin Plot", 
            "Heatmap", "Summary"
        ])
        self.plot_type_combo.currentTextChanged.connect(self.on_plot_type_changed)
        plot_gen_layout.addWidget(self.plot_type_combo, 0, 1)
        
        # Color by selector
        plot_gen_layout.addWidget(QLabel("Color by:"), 1, 0)
        self.color_by_combo = QComboBox()
        plot_gen_layout.addWidget(self.color_by_combo, 1, 1)
        
        # Gene selector (for applicable plots)
        plot_gen_layout.addWidget(QLabel("Gene:"), 2, 0)
        self.gene_combo = QComboBox()
        self.gene_combo.setEditable(True)
        plot_gen_layout.addWidget(self.gene_combo, 2, 1)
        
        # Generate plot button
        self.generate_plot_btn = QPushButton("🎯 Generate Plot")
        self.generate_plot_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.generate_plot_btn.clicked.connect(self.generate_custom_plot)
        plot_gen_layout.addWidget(self.generate_plot_btn, 3, 0, 1, 2)
        
        plot_gen_group.setLayout(plot_gen_layout)
        layout.addWidget(plot_gen_group)
        
        # Plot Options
        options_group = QGroupBox("🎚️ Plot Options")
        options_layout = QGridLayout()
        
        # DPI setting
        options_layout.addWidget(QLabel("Quality (DPI):"), 0, 0)
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(300)
        options_layout.addWidget(self.dpi_spin, 0, 1)
        
        # Size setting
        options_layout.addWidget(QLabel("Size (inches):"), 1, 0)
        self.size_combo = QComboBox()
        self.size_combo.addItems(["6x4", "8x6", "10x8", "12x9"])
        self.size_combo.setCurrentText("6x4")
        options_layout.addWidget(self.size_combo, 1, 1)
        
        # Auto-save checkbox
        self.auto_save_check = QCheckBox("Auto-save generated plots")
        self.auto_save_check.setChecked(True)
        options_layout.addWidget(self.auto_save_check, 2, 0, 1, 2)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Quick Actions
        quick_group = QGroupBox("⚡ Quick Actions")
        quick_layout = QGridLayout()
        
        # UMAP + Leiden button
        umap_leiden_btn = QPushButton("UMAP + Clusters")
        umap_leiden_btn.clicked.connect(lambda: self.quick_plot("UMAP", "leiden"))
        quick_layout.addWidget(umap_leiden_btn, 0, 0)
        
        # UMAP + Doublet Score button  
        umap_doublet_btn = QPushButton("UMAP + Doublet Score")
        umap_doublet_btn.clicked.connect(lambda: self.quick_plot("UMAP", "doublet_score"))
        quick_layout.addWidget(umap_doublet_btn, 0, 1)
        
        # PCA + Clusters button
        pca_leiden_btn = QPushButton("PCA + Clusters")
        pca_leiden_btn.clicked.connect(lambda: self.quick_plot("PCA", "leiden"))
        quick_layout.addWidget(pca_leiden_btn, 1, 0)
        
        # QC Metrics button
        qc_btn = QPushButton("QC Overview")
        qc_btn.clicked.connect(lambda: self.quick_plot("QC Metrics", None))
        quick_layout.addWidget(qc_btn, 1, 1)
        
        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_menu_bar(self):
        """Create the main menu bar without icons"""
        self.menu_bar = self.menuBar()
        
        # File Menu
        file_menu = self.menu_bar.addMenu("File")
        
        new_action = QAction("New Project", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.create_new_project)
        file_menu.addAction(new_action)
        
        import_action = QAction("Import Data", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)

        load_action = QAction("Load Results", self)
        load_action.setShortcut(QKeySequence("Ctrl+L"))
        load_action.triggered.connect(self.load_previous_results)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()

        self.recent_menu = file_menu.addMenu("Open Recent")
        self.update_recent_menu(self.recent_menu)

        file_menu.addSeparator()
        
        save_action = QAction("Save Project", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save Project As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        export_menu = file_menu.addMenu("Export")
        export_data_action = QAction("Export AnnData (.h5ad)", self)
        export_data_action.triggered.connect(self.export_analysis_data)
        export_menu.addAction(export_data_action)
        
        export_plots_action = QAction("Export All Plots", self)
        export_plots_action.triggered.connect(self.export_plots)
        export_menu.addAction(export_plots_action)

        file_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Analysis Menu
        analysis_menu = self.menu_bar.addMenu("Analysis")
        
        run_analysis_action = QAction("Run QC to Cluster", self)
        run_analysis_action.setShortcut("Ctrl+R")
        run_analysis_action.triggered.connect(self.run_standard_analysis)
        analysis_menu.addAction(run_analysis_action)

        analysis_menu.addSeparator()

        qc_menu = analysis_menu.addMenu("QC Steps")
        qc_menu.addAction("Calculate QC Metrics", self.calculate_qc_metrics)
        qc_menu.addAction("Filter Cells", self.filter_cells)
        qc_menu.addAction("Filter Genes", self.filter_genes)
        
        processing_menu = analysis_menu.addMenu("Processing Steps")
        processing_menu.addAction("Log Normalize", self.log_normalize)
        processing_menu.addAction("Scale Data", self.scale_data)
        
        dim_red_menu = analysis_menu.addMenu("Dimensionality Reduction")
        dim_red_menu.addAction("Run PCA", self.run_pca)
        dim_red_menu.addAction("Run UMAP", self.run_umap)
        dim_red_menu.addAction("Run t-SNE", self.run_tsne)
        
        cluster_menu = analysis_menu.addMenu("Clustering")
        cluster_menu.addAction("Leiden Clustering", self.leiden_clustering)
        cluster_menu.addAction("Louvain Clustering", self.louvain_clustering)

        # Documentation Menu
        doc_menu = self.menu_bar.addMenu("Help")
        
        doc_menu.addAction("Getting Started", self.show_getting_started)
        doc_menu.addAction("User Manual", self.show_user_manual)
        doc_menu.addAction("Tutorials", self.show_tutorials)
        doc_menu.addSeparator()
        doc_menu.addAction("Download Sample Data", self.download_sample_data)
        doc_menu.addSeparator()
        doc_menu.addAction("About SingleCellStudio", self.show_about)
        doc_menu.addAction("Version Info", self.show_version_info)

    def create_toolbar(self):
        """Toolbar is disabled for a cleaner, menu-driven interface"""
        pass

    def create_status_bar(self):
        """Create professional status bar"""
        status_bar = self.statusBar()
        status_bar.showMessage("SingleCellStudio Professional - Ready")
        
        # Add permanent widgets
        self.progress_label = QLabel("Ready")
        status_bar.addPermanentWidget(self.progress_label)
        
        self.memory_label = QLabel("Memory: 0 MB")
        status_bar.addPermanentWidget(self.memory_label)
        
        # Update memory usage periodically
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_usage)
        self.memory_timer.start(5000)  # Update every 5 seconds
    
    def apply_professional_styling(self):
        """Apply professional styling to the interface"""
        try:
            # Load QSS stylesheet from file
            qss_file = Path(__file__).parent / "default.qss"
            if qss_file.exists():
                with open(qss_file, 'r', encoding='utf-8') as f:
                    qss_content = f.read()
                self.setStyleSheet(qss_content)
                self.log_activity("Applied professional QSS styling")
            else:
                # Fallback to basic styling if QSS file not found
                self.apply_fallback_styling()
                self.log_activity("QSS file not found, using fallback styling")
        except Exception as e:
            self.log_activity(f"Error loading QSS stylesheet: {e}")
            self.apply_fallback_styling()
    
    def apply_fallback_styling(self):
        """Apply fallback styling if QSS file is not available"""
        style = """
        QMainWindow {
            background-color: #f8f9fa;
            color: #212529;
        }
        
        QTabWidget::pane {
            border: 1px solid #dee2e6;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #e9ecef;
            border: 1px solid #dee2e6;
            padding: 8px 16px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 1px solid white;
        }
        
        QTabBar::tab:hover {
            background-color: #f8f9fa;
        }
        
        QPushButton {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #0056b3;
        }
        
        QPushButton:pressed {
            background-color: #004085;
        }
        
        QPushButton:disabled {
            background-color: #6c757d;
            color: #ffffff;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
        }
        
        QSpinBox, QDoubleSpinBox, QComboBox {
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 4px 8px;
            background-color: white;
        }
        
        QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border-color: #007bff;
            outline: none;
        }
        
        QTextEdit {
            border: 1px solid #ced4da;
            border-radius: 4px;
            background-color: white;
            font-family: 'Courier New', monospace;
        }
        
        QProgressBar {
            border: 1px solid #ced4da;
            border-radius: 4px;
            text-align: center;
            background-color: #e9ecef;
        }
        
        QProgressBar::chunk {
            background-color: #28a745;
            border-radius: 3px;
        }
        """
        self.setStyleSheet(style)
    
    def setup_connections(self):
        """Set up signal connections"""
        # Tab change handler
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    # Utility methods
    def _setup_output_directory(self):
        """Set up output directory based on input file location"""
        if self.input_file_path:
            # Create results folder next to input file
            input_path = Path(self.input_file_path)
            base_dir = input_path.parent
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = base_dir / f"results_{input_path.stem}_{timestamp}"
        else:
            # Create results folder in current directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(f"results/analysis_results_{timestamp}")
        
        # Create directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Output directory set up: {output_dir.absolute()}")
        return output_dir
    
    def log_activity(self, message):
        """Log activity to the activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        current_text = self.activity_log.toPlainText()
        new_text = f"[{timestamp}] {message}\n{current_text}"
        self.activity_log.setText(new_text)
        logger.info(message)
    
    def update_memory_usage(self):
        """Update memory usage display"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"Memory: {memory_mb:.1f} MB")
        except ImportError:
            self.memory_label.setText("Memory: N/A")
    
    # Menu Action Methods
    def create_new_project(self):
        """Create a new analysis project"""
        self.log_activity("Creating new project...")
        
        # Reset interface
        self.adata = None
        self.analysis_adata = None
        self.analysis_results = None
        self.input_file_path = None
        self.output_dir = None
        
        # Update UI
        self.current_mode = "welcome"
        self.data_info_label.setText("No data loaded")
        self.data_header.setText("No data loaded")
        self.tab_widget.setCurrentIndex(0)
        self.tab_widget.setTabEnabled(1, False)
        self.tab_widget.setTabEnabled(2, False)
        
        self.statusBar().showMessage("New project created")
    
    def open_recent(self):
        """Open recent project"""
        QMessageBox.information(self, "Feature Coming Soon", 
                              "Recent projects functionality will be available in the next version.")
    
    def import_data(self):
        """Import single cell data using professional dialog"""
        self.log_activity("Opening data import dialog...")
        
        # Try to import DataImportDialog if not available
        dialog_class = DataImportDialog
        if dialog_class is None:
            try:
                from .data_import_dialog import DataImportDialog as dialog_class
            except ImportError:
                try:
                    from data_import_dialog import DataImportDialog as dialog_class
                except ImportError:
                    QMessageBox.warning(
                        self,
                        "Import Not Available",
                        "Data import functionality is not available.\n\n"
                        "Please ensure all required dependencies are installed."
                    )
                    return
        
        dialog = dialog_class(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the loaded data and file path
            self.adata = dialog.get_loaded_data()
            self.input_file_path = dialog.get_file_path()
            
            if self.adata is not None:
                self.log_activity(f"Data loaded: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes")
                
                # Set up output directory
                self.output_dir = self._setup_output_directory()
                
                # Update UI
                self.current_mode = "data_loaded"
                self.data_info_label.setText(f"📊 {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes")
                self.data_header.setText(f"📊 Dataset: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes")
                
                # Enable QC & Cluster tab for analysis
                self.tab_widget.setTabEnabled(1, True)  # QC & Cluster
                # Cell Annotation tab remains disabled until clustering is complete
                self.tab_widget.setCurrentIndex(1)
                
                # Update annotation widget with new data (but it will remain disabled until clustering)
                self.update_annotation_widget_data()
                
                self.statusBar().showMessage(
                    f"Data loaded: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes"
                )
    
    def load_previous_results(self):
        """Load analysis results from a previous session"""
        self.log_activity("Loading previous analysis results...")
        
        # Open folder dialog to select results directory
        results_dir = QFileDialog.getExistingDirectory(
            self, 
            "Select Results Directory",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not results_dir:
            return
        
        results_path = Path(results_dir)
        
        try:
            # Look for analysis result files with much broader patterns
            h5ad_files = []
            
            # First, try to find common final result patterns
            patterns = [
                "**/intermediate_data/*clustering*.h5ad",
                "**/intermediate_data/*final*.h5ad", 
                "**/*clustering*.h5ad",
                "**/*final*.h5ad",
                "**/intermediate_data/*.h5ad",
                "**/*.h5ad"
            ]
            
            for pattern in patterns:
                files = list(results_path.glob(pattern))
                h5ad_files.extend(files)
            
            # Remove duplicates
            h5ad_files = list(set(h5ad_files))
            
            if not h5ad_files:
                # Show detailed diagnostic information
                all_files = list(results_path.glob("**/*"))
                file_info = "\n".join([f"  {f.relative_to(results_path)}" for f in all_files[:20]])
                QMessageBox.warning(
                    self, "No Results Found", 
                    f"No analysis result files (.h5ad) found in:\n{results_dir}\n\n"
                    f"Files found:\n{file_info}{'...' if len(all_files) > 20 else ''}"
                )
                return
            
            # Use the most recent file, preferring clustering results
            clustering_files = [f for f in h5ad_files if 'clustering' in f.name.lower()]
            if clustering_files:
                result_file = max(clustering_files, key=lambda f: f.stat().st_mtime)
            else:
                result_file = max(h5ad_files, key=lambda f: f.stat().st_mtime)
            
            self.log_activity(f"Loading result file: {result_file.relative_to(results_path)}")
            
            # Load the analysis results
            import anndata as ad
            self.analysis_adata = ad.read_h5ad(result_file)
            self.adata = self.analysis_adata.copy()  # Also set as current data
            self.output_dir = results_path
            
            # Update UI state
            self.current_mode = "analysis_complete"
            
            # Update displays
            self.data_info_label.setText(f"📊 {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes")
            self.data_header.setText(f"📊 Dataset: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes (Loaded Results)")
            
            # Enable all tabs
            self.tab_widget.setTabEnabled(1, True)
            self.tab_widget.setTabEnabled(2, True)
            
            # Switch to results tab
            self.tab_widget.setCurrentIndex(2)
            
            # Update results summary
            n_clusters = len(self.adata.obs['leiden'].unique()) if 'leiden' in self.adata.obs else 'N/A'
            n_variable_genes = self.adata.var['highly_variable'].sum() if 'highly_variable' in self.adata.var else 'N/A'
            
            self.summary_text.setText(f"""Previous Analysis Results Loaded!

📊 Dataset: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes
📁 Results from: {results_path.name}
📅 Last modified: {result_file.stat().st_mtime}

Key Results:
• Clusters identified: {n_clusters}
• Variable genes: {n_variable_genes}
• Analysis data loaded: ✅
• Ready for visualization: ✅

Results loaded from: {results_dir}""")
            
            # Load and display plots
            self.load_analysis_plots()
            
            self.log_activity(f"Previous results loaded successfully from: {results_path.name}")
            self.statusBar().showMessage(f"Results loaded: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes")
            
            # Update plot generation controls
            self.update_plot_controls()
            
            # Update annotation widget with loaded data
            self.update_annotation_widget_data()
            
        except Exception as e:
            self.log_activity(f"Error loading results: {str(e)}")
            QMessageBox.critical(
                self, "Error Loading Results", 
                f"Failed to load analysis results:\n\n{str(e)}"
            )
    
    def save_project(self):
        """Save current project"""
        if self.adata is None:
            QMessageBox.information(self, "No Data", "No data to save. Please import data first.")
            return
        
        QMessageBox.information(self, "Feature Coming Soon", 
                              "Project saving functionality will be available in the next version.")
    
    def save_project_as(self):
        """Save project with new name"""
        self.save_project()
    
    def run_standard_analysis(self):
        """Run the standard analysis pipeline"""
        if self.adata is None:
            QMessageBox.warning(self, "No Data", "Please import data before running analysis.")
            return

        # Clear previous logs
        self.progress_log_display.clear()
        self.log_activity("Starting QC to Cluster pipeline...")
        
        try:
            # Collect parameters from the UI
            pipeline_params = {
                'min_genes': self.min_genes_spin.value(),
                'min_cells': self.min_cells_spin.value(),
                'target_sum': self.target_sum_spin.value(),
                'n_top_genes': self.n_var_genes_spin.value(),
                'n_pcs': self.n_pca_spin.value(),
                'resolution': self.resolution_spin.value()
            }
            
            self.log_activity(f"Analysis parameters: {pipeline_params}")

            # Disable run button to prevent multiple clicks
            self.run_analysis_btn.setEnabled(False)
            
            # Start analysis worker
            self.worker = AnalysisWorker(self.adata, pipeline_params, self.output_dir)
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.analysis_completed.connect(self.analysis_completed)
            self.worker.analysis_failed.connect(self.analysis_failed)
            
            # Show progress
            self.progress_bar.setVisible(True)
            self.update_progress(0, "Starting QC to Cluster pipeline...")
            self.current_mode = "analysis_running"
            
            self.worker.start()
            
        except Exception as e:
            self.log_activity(f"Error starting standard analysis: {str(e)}")
            QMessageBox.critical(self, "Analysis Error", 
                               f"Failed to start standard analysis:\n\n{str(e)}")
            self.run_analysis_btn.setEnabled(True)
    
    def update_progress(self, value, message):
        """Update progress bar and log display"""
        self.progress_bar.setValue(value)
        self.statusBar().showMessage(message)
        
        # Append message to the log display
        if hasattr(self, 'progress_log_display'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.progress_log_display.append(f"[{timestamp}] {message}")
    
    def analysis_completed(self, adata, results):
        """Handle successful analysis completion"""
        self.analysis_adata = adata
        self.analysis_results = results
        
        # Also update the main data with the processed results
        self.adata = adata
        
        self.log_activity("Analysis completed successfully!")
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        self.current_mode = "analysis_complete"
        
        # Enable and switch to QC & Cluster results tab
        self.tab_widget.setTabEnabled(1, True)
        self.tab_widget.setCurrentIndex(1)
        
        # Enable Cell Annotation tab now that clustering is complete
        self.tab_widget.setTabEnabled(2, True)
        
        # Update annotation widget with processed data
        self.update_annotation_widget_data()
        
        # Update results display
        n_clusters = len(adata.obs['leiden'].unique()) if 'leiden' in adata.obs else 'N/A'
        n_variable_genes = adata.var['highly_variable'].sum() if 'highly_variable' in adata.var else 'N/A'
        
        self.summary_text.setText(f"""Analysis Completed Successfully!

📊 Dataset: {adata.n_obs:,} cells × {adata.n_vars:,} genes
🔬 Analysis Steps: {len(results.get('steps', []))} completed
📁 Output: {self.output_dir}

Key Results:
• Clusters identified: {n_clusters}
• Variable genes: {n_variable_genes}
• QC metrics calculated: ✅
• Normalization: ✅
• Dimensionality reduction: ✅
• Clustering: ✅

All results saved to: {self.output_dir}""")
        
        # Generate standard plots automatically
        self.generate_standard_plots()
        
        # Load and display plots
        self.load_analysis_plots()
        
        # Update plot generation controls
        self.update_plot_controls()
        
        # Add a debug button for testing plot loading
        self.add_debug_plot_info()
        
        self.statusBar().showMessage("Analysis completed successfully!", 5000)
    
    def load_analysis_plots(self):
        """Load and display analysis plots"""
        if not MATPLOTLIB_AVAILABLE:
            self.log_activity("Matplotlib not available for plot display")
            return
        
        if self.output_dir is None:
            self.log_activity("No output directory set")
            return
        
        plots_dir = self.output_dir / "plots"
        if not plots_dir.exists():
            self.log_activity(f"Plots directory not found: {plots_dir}")
            # List what directories do exist
            existing_dirs = [d for d in self.output_dir.iterdir() if d.is_dir()]
            if existing_dirs:
                self.log_activity(f"Available directories: {[d.name for d in existing_dirs]}")
            return
        
        # Check what plot files exist
        all_plot_files = (
            list(plots_dir.glob("*.png")) +
            list(plots_dir.glob("*.pdf")) +
            list(plots_dir.glob("*.svg")) +
            list(plots_dir.glob("*.jpg"))
        )
        self.log_activity(f"Found {len(all_plot_files)} plot files in {plots_dir}")
        
        if all_plot_files:
            self.log_activity(f"Available plots: {[f.name for f in all_plot_files[:10]]}{'...' if len(all_plot_files) > 10 else ''}")
        
        try:
            # Load plots with more flexible matching
            plots_loaded = 0
            
            # Load summary plot
            if self.load_plot_to_canvas(self.summary_canvas, plots_dir, "summary"):
                plots_loaded += 1
            
            # Load UMAP plot
            if self.load_plot_to_canvas(self.umap_canvas, plots_dir, "umap"):
                plots_loaded += 1
            
            # Load QC plot
            if self.load_plot_to_canvas(self.qc_canvas, plots_dir, "qc"):
                plots_loaded += 1
            
            # Load PCA plot
            if self.load_plot_to_canvas(self.pca_canvas, plots_dir, "pca"):
                plots_loaded += 1
            
            self.log_activity(f"Successfully loaded {plots_loaded}/4 analysis plots")
            
        except Exception as e:
            self.log_activity(f"Error loading plots: {str(e)}")
    
    def load_plot_to_canvas(self, canvas, plots_dir, plot_type):
        """Load a specific plot to canvas"""
        
        # Look for plot files with much broader patterns and extensions
        patterns = [
            f"{plot_type}_*.png",
            f"{plot_type}_*.pdf", 
            f"{plot_type}_*.jpg",
            f"*{plot_type}*.png",
            f"*{plot_type}*.pdf",
            f"*{plot_type}*.jpg",
            f"{plot_type}.png",
            f"{plot_type}.pdf",
            f"{plot_type}.jpg"
        ]
        
        plot_file = None
        matched_pattern = None
        
        for pattern in patterns:
            files = list(plots_dir.glob(pattern))
            if files:
                # Sort by modification time, take the most recent
                plot_file = max(files, key=lambda f: f.stat().st_mtime)
                matched_pattern = pattern
                break
        
        if plot_file and plot_file.exists():
            try:
                # Clear the canvas
                canvas.figure.clear()
                
                # Load and display the image
                img = plt.imread(str(plot_file))
                ax = canvas.figure.add_subplot(111)
                ax.imshow(img)
                ax.axis('off')  # Hide axes
                
                # Set title with file info
                ax.set_title(f"{plot_type.upper()} Plot ({plot_file.name})", 
                           fontsize=10, fontweight='bold')
                
                canvas.figure.tight_layout()
                canvas.draw()
                
                self.log_activity(f"Loaded {plot_type} plot: {plot_file.name}")
                return True
                
            except Exception as e:
                self.log_activity(f"Failed to load {plot_type} plot {plot_file.name}: {str(e)}")
                self._show_plot_error(canvas, plot_type, f"Error loading: {str(e)}")
                return False
        else:
            # Show diagnostic info about what files were found
            all_files = list(plots_dir.glob("*"))
            matching_files = []
            for pattern in [f"*{plot_type}*", f"{plot_type}*"]:
                matching_files.extend(plots_dir.glob(pattern))
            
            if matching_files:
                file_list = [f.name for f in matching_files[:5]]
                message = f"Found {len(matching_files)} files with '{plot_type}' but none loadable:\n{', '.join(file_list)}"
            else:
                message = f"No {plot_type} plot found\nSearched for: {', '.join(patterns[:3])}..."
            
            self._show_plot_error(canvas, plot_type, message)
            return False
    
    def _show_plot_error(self, canvas, plot_type, message):
        """Show error message on canvas"""
        canvas.figure.clear()
        ax = canvas.figure.add_subplot(111)
        ax.text(0.5, 0.5, message, 
               horizontalalignment='center', verticalalignment='center',
               transform=ax.transAxes, fontsize=10, wrap=True)
        ax.set_title(f"{plot_type.upper()} Plot - Not Available", fontsize=12)
        ax.axis('off')
        canvas.draw()
    
    def add_debug_plot_info(self):
        """Add debug information about plot loading"""
        if self.output_dir and (self.output_dir / "plots").exists():
            plots_dir = self.output_dir / "plots"
            all_files = list(plots_dir.glob("*"))
            self.log_activity(f"Debug: Plots directory has {len(all_files)} files")
            
            # Show first few files for debugging
            if all_files:
                sample_files = [f.name for f in all_files[:5]]
                self.log_activity(f"Debug: Sample files: {sample_files}")
    
    def update_plot_controls(self):
        """Update plot generation controls based on loaded data"""
        if self.adata is None:
            return
        
        # Update color by options
        self.color_by_combo.clear()
        
        # Add categorical columns
        categorical_cols = []
        for col in self.adata.obs.columns:
            if self.adata.obs[col].dtype == 'category' or self.adata.obs[col].dtype == 'object':
                categorical_cols.append(col)
        
        # Add numerical columns
        numerical_cols = []
        for col in self.adata.obs.columns:
            if self.adata.obs[col].dtype in ['int64', 'float64']:
                numerical_cols.append(col)
        
        # Populate color by combo
        if 'leiden' in categorical_cols:
            self.color_by_combo.addItem('leiden')
        
        for col in sorted(categorical_cols):
            if col != 'leiden':
                self.color_by_combo.addItem(col)
        
        if numerical_cols:
            self.color_by_combo.addItem("--- Numerical ---")
            for col in sorted(numerical_cols):
                self.color_by_combo.addItem(col)
        
        # Update gene options
        self.gene_combo.clear()
        # Add some common marker genes if they exist
        common_genes = ['CD3D', 'CD3E', 'CD8A', 'CD4', 'CD19', 'MS4A1', 'CD14', 'LYZ', 'FCGR3A', 'PPBP']
        for gene in common_genes:
            if gene in self.adata.var_names:
                self.gene_combo.addItem(gene)
        
        # Add separator and all genes
        if self.gene_combo.count() > 0:
            self.gene_combo.addItem("--- All Genes ---")
        
        # Add first 100 genes for performance
        for gene in sorted(self.adata.var_names[:100]):
            self.gene_combo.addItem(gene)
    
    def on_plot_type_changed(self, plot_type):
        """Handle plot type change"""
        # Enable/disable gene selector based on plot type
        gene_based_plots = ["Violin Plot", "Heatmap"]
        self.gene_combo.setEnabled(plot_type in gene_based_plots)
    
    def quick_plot(self, plot_type, color_by):
        """Generate a quick plot with predefined settings"""
        if self.adata is None:
            QMessageBox.warning(self, "No Data", "No analysis data available for plotting.")
            return
        
        # Set the controls to match the quick plot
        self.plot_type_combo.setCurrentText(plot_type)
        if color_by and color_by in [self.color_by_combo.itemText(i) for i in range(self.color_by_combo.count())]:
            self.color_by_combo.setCurrentText(color_by)
        
        # Generate the plot
        self.generate_custom_plot()
    
    def generate_custom_plot(self):
        """Generate a custom plot based on current settings"""
        if self.adata is None:
            QMessageBox.warning(self, "No Data", "No analysis data available for plotting.")
            return
        
        try:
            import scanpy as sc
            import matplotlib.pyplot as plt
            
            plot_type = self.plot_type_combo.currentText()
            color_by = self.color_by_combo.currentText()
            gene = self.gene_combo.currentText()
            
            # Get size settings
            size_str = self.size_combo.currentText()
            width, height = map(int, size_str.split('x'))
            dpi = self.dpi_spin.value()
            
            # Skip separator items
            if color_by.startswith("---"):
                color_by = "leiden"
            
            # Validate color_by column exists
            if color_by not in self.adata.obs.columns:
                if 'leiden' in self.adata.obs.columns:
                    color_by = 'leiden'
                else:
                    color_by = None
            
            # Create the plot based on type
            fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
            
            if plot_type == "UMAP":
                if 'X_umap' in self.adata.obsm:
                    sc.pl.umap(self.adata, color=color_by, ax=ax, show=False)
                    title = f"UMAP - {color_by}" if color_by else "UMAP"
                else:
                    ax.text(0.5, 0.5, "UMAP coordinates not available", 
                           ha='center', va='center', transform=ax.transAxes)
                    title = "UMAP - Not Available"
                    
            elif plot_type == "PCA":
                if 'X_pca' in self.adata.obsm:
                    sc.pl.pca(self.adata, color=color_by, ax=ax, show=False)
                    title = f"PCA - {color_by}" if color_by else "PCA"
                else:
                    ax.text(0.5, 0.5, "PCA coordinates not available", 
                           ha='center', va='center', transform=ax.transAxes)
                    title = "PCA - Not Available"
                    
            elif plot_type == "QC Metrics":
                # Create QC metrics plot
                qc_metrics = ['n_genes_by_counts', 'total_counts']
                if 'pct_counts_mt' in self.adata.obs.columns:
                    qc_metrics.append('pct_counts_mt')
                
                available_metrics = [m for m in qc_metrics if m in self.adata.obs.columns]
                if available_metrics:
                    sc.pl.violin(self.adata, available_metrics[:3], jitter=0.4, 
                               multi_panel=True, ax=ax, show=False)
                    title = "QC Metrics"
                else:
                    ax.text(0.5, 0.5, "QC metrics not available", 
                           ha='center', va='center', transform=ax.transAxes)
                    title = "QC Metrics - Not Available"
                    
            elif plot_type == "Violin Plot" and gene:
                if gene in self.adata.var_names and color_by:
                    sc.pl.violin(self.adata, gene, groupby=color_by, ax=ax, show=False)
                    title = f"Violin Plot - {gene} by {color_by}"
                else:
                    ax.text(0.5, 0.5, f"Gene '{gene}' or grouping '{color_by}' not available", 
                           ha='center', va='center', transform=ax.transAxes)
                    title = "Violin Plot - Not Available"
                    
            elif plot_type == "Heatmap":
                # Simple heatmap with top variable genes
                if 'highly_variable' in self.adata.var.columns:
                    hvg = self.adata[:, self.adata.var['highly_variable']].var_names[:20]
                    sc.pl.heatmap(self.adata, hvg, groupby=color_by, ax=ax, show=False)
                    title = f"Top Variable Genes - {color_by}"
                else:
                    ax.text(0.5, 0.5, "Variable genes not available", 
                           ha='center', va='center', transform=ax.transAxes)
                    title = "Heatmap - Not Available"
                    
            else:  # Summary
                # Create a simple summary plot
                ax.text(0.5, 0.7, f"Dataset Summary", ha='center', va='center', 
                       transform=ax.transAxes, fontsize=16, fontweight='bold')
                ax.text(0.5, 0.5, f"Cells: {self.adata.n_obs:,}\nGenes: {self.adata.n_vars:,}", 
                       ha='center', va='center', transform=ax.transAxes, fontsize=14)
                if 'leiden' in self.adata.obs.columns:
                    n_clusters = len(self.adata.obs['leiden'].unique())
                    ax.text(0.5, 0.3, f"Clusters: {n_clusters}", ha='center', va='center', 
                           transform=ax.transAxes, fontsize=14)
                title = "Dataset Summary"
            
            ax.set_title(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            
            # Add to plots display
            self.add_generated_plot_to_display(fig, title)
            
            # Auto-save if enabled
            if self.auto_save_check.isChecked() and self.output_dir:
                self.save_generated_plot(fig, title)
            
            self.log_activity(f"Generated plot: {title}")
            
        except Exception as e:
            self.log_activity(f"Plot generation failed: {str(e)}")
            QMessageBox.critical(self, "Plot Generation Failed", 
                               f"Failed to generate plot:\n\n{str(e)}")
    
    def add_generated_plot_to_display(self, figure, title):
        """Add a generated plot to the display tabs"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        # Create new tab for generated plot
        plot_widget = QWidget()
        plot_layout = QVBoxLayout()
        
        canvas = FigureCanvas(figure)
        plot_layout.addWidget(canvas)
        plot_widget.setLayout(plot_layout)
        
        # Add tab with unique name
        tab_name = f"Generated: {title[:15]}..."
        self.plots_tabs.addTab(plot_widget, tab_name)
        
        # Switch to the new tab
        self.plots_tabs.setCurrentWidget(plot_widget)
    
    def save_generated_plot(self, figure, title):
        """Save a generated plot to the output directory"""
        if not self.output_dir:
            return
        
        try:
            plots_dir = self.output_dir / "plots"
            plots_dir.mkdir(exist_ok=True)
            
            # Create safe filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"custom_{safe_title}_{timestamp}"
            saved_files = []

            for ext in ('.png', '.pdf'):
                filepath = plots_dir / f"{base_filename}{ext}"
                save_kwargs = {'bbox_inches': 'tight'}
                if ext == '.png':
                    save_kwargs['dpi'] = 300
                figure.savefig(filepath, **save_kwargs)
                saved_files.append(filepath.name)

            self.log_activity(f"Plot saved: {', '.join(saved_files)}")
            
        except Exception as e:
            self.log_activity(f"Failed to save plot: {str(e)}")
    
    def generate_standard_plots(self):
        """Generate standard analysis plots automatically after pipeline completion"""
        if self.analysis_adata is None:
            self.log_activity("No analysis data available for standard plot generation")
            return
        
        self.log_activity("Generating standard analysis plots...")
        
        try:
            import scanpy as sc
            import matplotlib.pyplot as plt
            
            # Create plots directory
            plots_dir = self.output_dir / "plots"
            plots_dir.mkdir(exist_ok=True)
            
            generated_plots = []
            
            # 1. Generate Summary Plot
            try:
                fig, axes = plt.subplots(2, 2, figsize=(12, 10))
                fig.suptitle('Analysis Summary', fontsize=16, fontweight='bold')
                
                # Top left: UMAP with clusters
                if 'X_umap' in self.analysis_adata.obsm and 'leiden' in self.analysis_adata.obs:
                    sc.pl.umap(self.analysis_adata, color='leiden', ax=axes[0,0], show=False, frameon=False)
                    axes[0,0].set_title('UMAP - Clusters')
                else:
                    axes[0,0].text(0.5, 0.5, 'UMAP not available', ha='center', va='center')
                    axes[0,0].set_title('UMAP - Clusters')
                
                # Top right: Gene counts histogram
                if 'n_genes_by_counts' in self.analysis_adata.obs:
                    axes[0,1].hist(self.analysis_adata.obs['n_genes_by_counts'], bins=50, alpha=0.7)
                    axes[0,1].set_xlabel('Genes per cell')
                    axes[0,1].set_ylabel('Frequency')
                    axes[0,1].set_title('Genes per Cell Distribution')
                else:
                    axes[0,1].text(0.5, 0.5, 'Gene counts not available', ha='center', va='center')
                    axes[0,1].set_title('Genes per Cell')
                
                # Bottom left: Total counts histogram
                if 'total_counts' in self.analysis_adata.obs:
                    axes[1,0].hist(self.analysis_adata.obs['total_counts'], bins=50, alpha=0.7)
                    axes[1,0].set_xlabel('Total counts per cell')
                    axes[1,0].set_ylabel('Frequency')
                    axes[1,0].set_title('Total Counts Distribution')
                else:
                    axes[1,0].text(0.5, 0.5, 'Total counts not available', ha='center', va='center')
                    axes[1,0].set_title('Total Counts')
                
                # Bottom right: Cluster sizes
                if 'leiden' in self.analysis_adata.obs:
                    cluster_counts = self.analysis_adata.obs['leiden'].value_counts().sort_index()
                    axes[1,1].bar(range(len(cluster_counts)), cluster_counts.values)
                    axes[1,1].set_xlabel('Cluster')
                    axes[1,1].set_ylabel('Cell count')
                    axes[1,1].set_title('Cluster Sizes')
                    axes[1,1].set_xticks(range(len(cluster_counts)))
                    axes[1,1].set_xticklabels(cluster_counts.index)
                else:
                    axes[1,1].text(0.5, 0.5, 'Clustering not available', ha='center', va='center')
                    axes[1,1].set_title('Cluster Sizes')
                
                plt.tight_layout()
                
                # Save summary plot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                for ext in ('.png', '.pdf'):
                    summary_file = plots_dir / f"summary_{timestamp}{ext}"
                    save_kwargs = {'bbox_inches': 'tight'}
                    if ext == '.png':
                        save_kwargs['dpi'] = 300
                    fig.savefig(summary_file, **save_kwargs)
                    generated_plots.append(summary_file)
                plt.close(fig)
                
            except Exception as e:
                self.log_activity(f"Failed to generate summary plot: {str(e)}")
            
            # 2. Generate UMAP Plot
            try:
                if 'X_umap' in self.analysis_adata.obsm and 'leiden' in self.analysis_adata.obs:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    sc.pl.umap(self.analysis_adata, color='leiden', ax=ax, show=False)
                    ax.set_title('UMAP - Leiden Clustering', fontsize=14, fontweight='bold')
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    for ext in ('.png', '.pdf'):
                        umap_file = plots_dir / f"umap_{timestamp}{ext}"
                        save_kwargs = {'bbox_inches': 'tight'}
                        if ext == '.png':
                            save_kwargs['dpi'] = 300
                        fig.savefig(umap_file, **save_kwargs)
                        generated_plots.append(umap_file)
                    plt.close(fig)
                    
            except Exception as e:
                self.log_activity(f"Failed to generate UMAP plot: {str(e)}")
            
            # 3. Generate QC Plot
            try:
                qc_metrics = []
                if 'n_genes_by_counts' in self.analysis_adata.obs:
                    qc_metrics.append('n_genes_by_counts')
                if 'total_counts' in self.analysis_adata.obs:
                    qc_metrics.append('total_counts')
                if 'pct_counts_mt' in self.analysis_adata.obs:
                    qc_metrics.append('pct_counts_mt')
                
                if qc_metrics:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sc.pl.violin(self.analysis_adata, qc_metrics[:3], jitter=0.4, 
                               multi_panel=True, ax=ax, show=False)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    for ext in ('.png', '.pdf'):
                        qc_file = plots_dir / f"qc_{timestamp}{ext}"
                        save_kwargs = {'bbox_inches': 'tight'}
                        if ext == '.png':
                            save_kwargs['dpi'] = 300
                        fig.savefig(qc_file, **save_kwargs)
                        generated_plots.append(qc_file)
                    plt.close(fig)
                    
            except Exception as e:
                self.log_activity(f"Failed to generate QC plot: {str(e)}")
            
            # 4. Generate PCA Plot
            try:
                if 'X_pca' in self.analysis_adata.obsm and 'leiden' in self.analysis_adata.obs:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    sc.pl.pca(self.analysis_adata, color='leiden', ax=ax, show=False)
                    ax.set_title('PCA - Leiden Clustering', fontsize=14, fontweight='bold')
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    for ext in ('.png', '.pdf'):
                        pca_file = plots_dir / f"pca_{timestamp}{ext}"
                        save_kwargs = {'bbox_inches': 'tight'}
                        if ext == '.png':
                            save_kwargs['dpi'] = 300
                        fig.savefig(pca_file, **save_kwargs)
                        generated_plots.append(pca_file)
                    plt.close(fig)
                    
            except Exception as e:
                self.log_activity(f"Failed to generate PCA plot: {str(e)}")
            
            self.log_activity(f"Generated {len(generated_plots)} standard analysis plots")
            if generated_plots:
                plot_names = [f.name for f in generated_plots]
                self.log_activity(f"Standard plots: {', '.join(plot_names)}")
            
        except Exception as e:
            self.log_activity(f"Error in standard plot generation: {str(e)}")
    
    def analysis_failed(self, error_message):
        """Handle analysis failure"""
        self.log_activity(f"Analysis failed: {error_message}")
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        self.current_mode = "data_loaded"
        self.run_analysis_btn.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Analysis Failed",
            f"Analysis pipeline failed with error:\n\n{error_message}"
        )
        
        self.statusBar().showMessage("Analysis failed", 5000)
    
    def on_annotation_completed(self, results):
        """Handle successful cell annotation completion"""
        self.log_activity("Cell annotation completed successfully!")
        
        # Update annotation visualizations
        self.update_annotation_visualizations(results)
        
        # Save final annotated data (this is the only save we need)
        self.save_final_annotated_data(results)
        
        # Show success message
        QMessageBox.information(
            self,
            "Cell Annotation Complete",
            f"Cell annotation completed successfully!\n\n"
            f"Method: {results.get('method_used', 'Unknown')}\n"
            f"Cell types identified: {len(results.get('summary', {}).get('cell_type_counts', {}))}\n"
            f"Mean confidence: {results.get('summary', {}).get('mean_confidence', 0):.3f}\n\n"
            f"Final results saved to: {self.output_dir}"
        )
    
    def save_final_annotated_data(self, annotation_results):
        """Save the final annotated data with all analysis and annotation results"""
        if self.adata is None or self.output_dir is None:
            return
        
        try:
            # Create final results directory
            final_dir = self.output_dir / "final_results"
            final_dir.mkdir(exist_ok=True)
            
            # Save the complete annotated dataset
            final_file = final_dir / "complete_analysis_with_annotation.h5ad"
            self.adata.write(final_file)
            
            # Save annotation results summary
            summary_file = final_dir / "annotation_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(annotation_results, f, indent=4, default=str)
            
            # Save a human-readable summary
            summary_text_file = final_dir / "analysis_summary.txt"
            with open(summary_text_file, 'w') as f:
                f.write("SingleCellStudio Analysis Summary\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Dataset: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes\n")
                f.write(f"Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # QC & Clustering results
                if 'leiden' in self.adata.obs:
                    n_clusters = len(self.adata.obs['leiden'].unique())
                    f.write(f"Clustering: {n_clusters} clusters identified\n")
                
                if 'highly_variable' in self.adata.var:
                    n_hvg = self.adata.var['highly_variable'].sum()
                    f.write(f"Variable genes: {n_hvg:,} highly variable genes\n")
                
                # Cell annotation results
                summary = annotation_results.get('summary', {})
                if summary:
                    f.write(f"\nCell Annotation Results:\n")
                    f.write(f"Method: {annotation_results.get('method_used', 'Unknown')}\n")
                    f.write(f"Unique cell types: {summary.get('unique_cell_types', 'N/A')}\n")
                    f.write(f"Mean confidence: {summary.get('mean_confidence', 0):.3f}\n")
                    f.write(f"High confidence cells: {summary.get('high_confidence_cells', 'N/A'):,}\n")
                    
                    # Cell type distribution
                    cell_type_counts = summary.get('cell_type_counts', {})
                    if cell_type_counts:
                        f.write(f"\nCell Type Distribution:\n")
                        total_cells = summary.get('total_cells', 1)
                        for cell_type, count in sorted(cell_type_counts.items(), key=lambda x: x[1], reverse=True):
                            percentage = (count / total_cells) * 100
                            f.write(f"  {cell_type}: {count:,} cells ({percentage:.1f}%)\n")
                
                f.write(f"\nFiles saved:\n")
                f.write(f"  - Complete dataset: {final_file.name}\n")
                f.write(f"  - Annotation results: {summary_file.name}\n")
                f.write(f"  - Analysis summary: {summary_text_file.name}\n")
            
            self.log_activity(f"Final annotated data saved: {final_file}")
            self.log_activity(f"Analysis summary saved: {summary_text_file}")
            
        except Exception as e:
            self.log_activity(f"Error saving final annotated data: {e}")
            QMessageBox.warning(
                self,
                "Save Error",
                f"Failed to save final results:\n\n{str(e)}"
            )
    
    def on_analysis_failed(self, error_message):
        """Handle general analysis failure (for modular components)"""
        try:
            self.log_activity(f"❌ Analysis failed: {error_message}")
            
            # Show error message
            QMessageBox.warning(self, "Analysis Failed", 
                              f"Analysis failed:\n\n{error_message}")
            
        except Exception as e:
            self.logger.error(f"Error handling analysis failure: {e}")
    
    def update_annotation_widget_data(self):
        """Update annotation widget with current data"""
        try:
            # Update the annotation widget in the dedicated cell annotation tab
            if hasattr(self, 'annotation_widget') and self.annotation_widget is not None:
                if self.adata is not None:
                    self.annotation_widget.set_data(self.adata)
                    self.log_activity("Advanced annotation widget updated with new data")
                else:
                    self.annotation_widget.clear_data()
                    self.log_activity("Advanced annotation widget data cleared")
            
            # Update color options in the annotation visualization
            if hasattr(self, 'annotation_color_combo') and self.adata is not None:
                # Update color options based on available data
                current_items = [self.annotation_color_combo.itemText(i) 
                               for i in range(self.annotation_color_combo.count())]
                
                # Add available columns
                available_columns = ['cell_type', 'annotation_confidence', 'leiden']
                for col in self.adata.obs.columns:
                    if col not in current_items and col not in available_columns:
                        available_columns.append(col)
                
                # Update combo box
                self.annotation_color_combo.clear()
                self.annotation_color_combo.addItems(available_columns)
                
        except Exception as e:
            self.logger.error(f"Error updating annotation widget: {e}")
    
    def update_annotation_visualizations(self, results):
        """Update the advanced annotation visualizations"""
        try:
            if not hasattr(self, 'annotation_viz_tabs') or self.adata is None:
                return
            
            # Update UMAP visualization
            self.refresh_annotation_umap()
            
            # Update proportions chart
            self.update_annotation_proportions(results)
            
            # Update confidence analysis
            self.update_annotation_confidence(results)
            
            # Update summary
            self.update_annotation_summary(results)
            
        except Exception as e:
            self.logger.error(f"Error updating annotation visualizations: {e}")
    
    def refresh_annotation_umap(self):
        """Refresh the annotation UMAP plot"""
        try:
            if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'annotation_umap_canvas'):
                return
            
            if self.adata is None or 'X_umap' not in self.adata.obsm:
                return
            
            color_by = self.annotation_color_combo.currentText()
            if color_by not in self.adata.obs.columns:
                return
            
            # Clear and create new plot
            self.annotation_umap_canvas.figure.clear()
            ax = self.annotation_umap_canvas.figure.add_subplot(111)
            
            # Plot UMAP
            umap_coords = self.adata.obsm['X_umap']
            colors = self.adata.obs[color_by]
            
            if colors.dtype.name == 'category' or colors.dtype == 'object':
                # Categorical coloring
                unique_vals = colors.unique()
                import matplotlib.pyplot as plt
                cmap = plt.cm.tab20(np.linspace(0, 1, len(unique_vals)))
                
                for i, val in enumerate(unique_vals):
                    mask = colors == val
                    ax.scatter(umap_coords[mask, 0], umap_coords[mask, 1], 
                             c=[cmap[i]], label=str(val), alpha=0.7, s=10)
                
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
            else:
                # Continuous coloring
                scatter = ax.scatter(umap_coords[:, 0], umap_coords[:, 1], 
                                   c=colors, alpha=0.7, s=10, cmap='viridis')
                self.annotation_umap_canvas.figure.colorbar(scatter, ax=ax)
            
            ax.set_xlabel('UMAP 1')
            ax.set_ylabel('UMAP 2')
            ax.set_title(f'UMAP colored by {color_by}')
            
            self.annotation_umap_canvas.figure.tight_layout()
            self.annotation_umap_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error refreshing annotation UMAP: {e}")
    
    def update_annotation_proportions(self, results):
        """Update cell type proportions chart"""
        try:
            if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'annotation_prop_canvas'):
                return
            
            summary = results.get('summary', {})
            cell_type_counts = summary.get('cell_type_counts', {})
            
            if not cell_type_counts:
                return
            
            # Clear and create new plot
            self.annotation_prop_canvas.figure.clear()
            ax = self.annotation_prop_canvas.figure.add_subplot(111)
            
            # Create pie chart
            labels = list(cell_type_counts.keys())
            sizes = list(cell_type_counts.values())
            
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title('Cell Type Proportions')
            
            self.annotation_prop_canvas.figure.tight_layout()
            self.annotation_prop_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error updating annotation proportions: {e}")
    
    def update_annotation_confidence(self, results):
        """Update confidence analysis chart"""
        try:
            if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'annotation_conf_canvas'):
                return
            
            if 'confidence' not in results or self.adata is None:
                return
            
            confidence_scores = results['confidence']
            
            # Clear and create new plot
            self.annotation_conf_canvas.figure.clear()
            ax = self.annotation_conf_canvas.figure.add_subplot(111)
            
            # Histogram of confidence scores
            ax.hist(confidence_scores, bins=20, alpha=0.7, edgecolor='black')
            ax.set_xlabel('Confidence Score')
            ax.set_ylabel('Number of Cells')
            ax.set_title('Annotation Confidence Distribution')
            ax.axvline(np.mean(confidence_scores), color='red', linestyle='--', 
                      label=f'Mean: {np.mean(confidence_scores):.3f}')
            ax.legend()
            
            self.annotation_conf_canvas.figure.tight_layout()
            self.annotation_conf_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error updating annotation confidence: {e}")
    
    def update_annotation_summary(self, results):
        """Update annotation summary text"""
        try:
            if not hasattr(self, 'annotation_summary_text'):
                return
            
            summary_lines = ["🧬 Cell Annotation Results", "=" * 40]
            
            method_used = results.get('method_used', 'Unknown')
            summary_lines.append(f"Method: {method_used}")
            summary_lines.append("")
            
            summary = results.get('summary', {})
            if summary:
                summary_lines.append("📊 Summary Statistics:")
                summary_lines.append(f"  Total cells: {summary.get('total_cells', 'N/A'):,}")
                summary_lines.append(f"  Unique cell types: {summary.get('unique_cell_types', 'N/A')}")
                summary_lines.append(f"  Mean confidence: {summary.get('mean_confidence', 0):.3f}")
                summary_lines.append(f"  High confidence cells: {summary.get('high_confidence_cells', 'N/A'):,}")
                summary_lines.append("")
                
                # Cell type distribution
                cell_type_counts = summary.get('cell_type_counts', {})
                if cell_type_counts:
                    summary_lines.append("🎯 Cell Type Distribution:")
                    total_cells = summary.get('total_cells', 1)
                    for cell_type, count in sorted(cell_type_counts.items(), key=lambda x: x[1], reverse=True):
                        percentage = (count / total_cells) * 100
                        summary_lines.append(f"  {cell_type}: {count:,} cells ({percentage:.1f}%)")
            
            # Method details
            method_details = results.get('method_details', {})
            if method_details and 'available_genes' in method_details:
                summary_lines.append("")
                summary_lines.append("🔬 Method Details:")
                available_genes = method_details['available_genes']
                for cell_type, genes_info in list(available_genes.items())[:5]:  # Show first 5
                    if isinstance(genes_info, dict):
                        pos_genes = genes_info.get('positive', [])
                        summary_lines.append(f"  {cell_type}: {len(pos_genes)} markers available")
            
            self.annotation_summary_text.setPlainText("\n".join(summary_lines))
            
        except Exception as e:
            self.logger.error(f"Error updating annotation summary: {e}")
    
    def on_tab_changed(self, index):
        """Handle tab change"""
        try:
            if index == 0:  # Home tab
                self.current_mode = "welcome" if self.adata is None else "data_loaded"
            elif index == 1:  # Analysis tab
                self.current_mode = "data_loaded"
            elif index == 2:  # Results tab
                self.current_mode = "analysis_complete"
        except Exception as e:
            self.logger.error(f"Error handling tab change: {e}")
    
    # Utility methods for menu updates
    def update_recent_menu(self, menu):
        """Update recent projects menu (placeholder)"""
        no_recent_action = QAction("No recent projects", self)
        no_recent_action.setEnabled(False)
        menu.addAction(no_recent_action)
    
    # Export and file operations
    def export_analysis_data(self):
        """Export analysis data"""
        if self.analysis_adata is None:
            QMessageBox.warning(self, "No Analysis Data", "No analysis data to export.")
            return
        
        QMessageBox.information(self, "Feature Coming Soon", 
                              "Analysis data export functionality will be available in the next version.")
    
    def export_plots(self):
        """Export plots"""
        if self.analysis_adata is None:
            QMessageBox.warning(self, "No Analysis Data", "No analysis data to export plots for.")
            return
        
        QMessageBox.information(self, "Feature Coming Soon", 
                              "Plot export functionality will be available in the next version.")
    
    def export_report(self):
        """Export analysis report"""
        QMessageBox.information(self, "Feature Coming Soon", 
                              "Analysis report export functionality will be available in the next version.")
    
    def refresh_plots_display(self):
        """Refresh plot display - useful for debugging"""
        if self.adata is None:
            QMessageBox.information(self, "No Data", "No analysis data loaded.")
            return
        
        self.log_activity("Refreshing plot display...")
        self.load_analysis_plots()
        self.log_activity("Plot refresh completed")
    
    def open_results_folder(self):
        """Open results folder"""
        if self.output_dir and self.output_dir.exists():
            import os
            import platform
            
            if platform.system() == "Windows":
                os.startfile(self.output_dir)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{self.output_dir}'")
            else:  # Linux
                os.system(f"xdg-open '{self.output_dir}'")
        else:
            QMessageBox.warning(self, "No Results", "No results folder available.")
    
    # Analysis method stubs
    def calculate_qc_metrics(self):
        """Calculate QC metrics"""
        QMessageBox.information(self, "Feature Coming Soon", "Individual QC metrics calculation will be available in the next version.")
    
    def filter_cells(self):
        """Filter cells"""
        QMessageBox.information(self, "Feature Coming Soon", "Individual cell filtering will be available in the next version.")
    
    def filter_genes(self):
        """Filter genes"""
        QMessageBox.information(self, "Feature Coming Soon", "Individual gene filtering will be available in the next version.")
    
    def log_normalize(self):
        """Log normalize data"""
        QMessageBox.information(self, "Feature Coming Soon", "Individual log normalization will be available in the next version.")
    
    def scale_data(self):
        """Scale data"""
        QMessageBox.information(self, "Feature Coming Soon", "Individual data scaling will be available in the next version.")
    
    def run_pca(self):
        """Run PCA"""
        QMessageBox.information(self, "Feature Coming Soon", "Individual PCA will be available in the next version.")
    
    def run_umap(self):
        """Run UMAP"""
        QMessageBox.information(self, "Feature Coming Soon", "Individual UMAP will be available in the next version.")
    
    def run_tsne(self):
        """Run t-SNE"""
        QMessageBox.information(self, "Feature Coming Soon", "Individual t-SNE will be available in the next version.")
    
    def leiden_clustering(self):
        """Leiden clustering"""
        QMessageBox.information(self, "Feature Coming Soon", "Individual Leiden clustering will be available in the next version.")
    
    def louvain_clustering(self):
        """Louvain clustering"""
        QMessageBox.information(self, "Feature Coming Soon", "Individual Louvain clustering will be available in the next version.")
    
    # Documentation methods
    def show_getting_started(self):
        """Show getting started guide"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Getting Started Guide")
        dialog.setMinimumSize(800, 600)
        dialog.resize(900, 700)
        
        layout = QVBoxLayout()
        
        # Create tabbed content
        tab_widget = QTabWidget()
        
        # Quick Start tab
        quick_start_text = QTextEdit()
        quick_start_text.setReadOnly(True)
        quick_start_text.setMarkdown("""
# Quick Start Guide

## 🚀 Getting Started with SingleCellStudio

### Step 1: Import Your Data
1. Click **"Import Single Cell Data"** on the home screen
2. Select your data file or folder:
   - **10X Genomics H5** files (.h5) - Recommended
   - **10X MTX folders** (matrix.mtx.gz + barcodes + features)
   - **AnnData files** (.h5ad)
   - **CSV/TSV files** with expression data

### Step 2: Quality Control & Clustering
1. Go to the **"QC & Cluster"** tab
2. Adjust parameters if needed:
   - **Min Genes per Cell**: 200 (filter low-quality cells)
   - **Min Cells per Gene**: 3 (filter rarely expressed genes)
   - **Target Sum**: 10,000 (normalization target)
   - **Variable Genes**: 2,000 (for dimensionality reduction)
   - **PCA Components**: 40 (principal components)
   - **Clustering Resolution**: 0.5 (cluster granularity)
3. Click **"Run QC to Cluster"**
4. Wait for analysis to complete (progress shown in log)

### Step 3: Cell Type Annotation
1. Go to the **"Cell Annotation"** tab (enabled after clustering)
2. Choose annotation method:
   - **Auto**: Recommended - selects best method automatically
   - **Reference-based**: Uses built-in cell type signatures
   - **Marker-based**: Uses known marker genes
3. Set confidence threshold: 0.5 (moderate confidence)
4. Click **"Run Analysis"**
5. Explore results in the visualization tabs

### Step 4: View Results
- **UMAP plots**: Colored by cell types, confidence, or clusters
- **Proportions**: Pie charts showing cell type distribution
- **Confidence**: Histograms of annotation confidence scores
- **Summary**: Detailed statistics and cell type counts

### Step 5: Export Results
- Use **"Export Data"** to save annotated dataset
- Use **"Export Plots"** to save visualization images
- Use **"Open Folder"** to access all result files

## 💡 Tips for Success
- **Start with good quality data**: Remove empty droplets and low-quality cells
- **Check clustering**: Ensure clusters make biological sense
- **Validate annotations**: Use known biology to verify cell type assignments
- **Experiment with parameters**: Adjust resolution for finer/coarser clusters
""")
        tab_widget.addTab(quick_start_text, "Quick Start")
        
        # Data Formats tab
        formats_text = QTextEdit()
        formats_text.setReadOnly(True)
        formats_text.setMarkdown("""
# Supported Data Formats

## 📁 Input Formats

### 1. 10X Genomics H5 Format ⭐ Recommended
**Single file containing everything:**
- `filtered_feature_bc_matrix.h5`
- Contains expression matrix, cell barcodes, and gene information
- Fast loading and memory efficient
- Preserves metadata and quality metrics

### 2. 10X Genomics MTX Format
**Folder containing three files:**
- `matrix.mtx.gz` - Sparse expression matrix
- `barcodes.tsv.gz` - Cell barcode identifiers
- `features.tsv.gz` - Gene information (ID, symbol, type)

**Alternative names supported:**
- Uncompressed versions (`.mtx`, `.tsv`)
- Legacy `genes.tsv.gz` instead of `features.tsv.gz`

### 3. AnnData H5AD Format
**Single file for processed data:**
- `data.h5ad` - Complete AnnData object
- Preserves all analysis results and metadata
- Compatible with scanpy and other tools
- Ideal for sharing processed datasets

### 4. CSV/TSV Format
**Tabular expression data:**
- `expression_data.csv` or `.tsv`
- Genes as columns, cells as rows (or vice versa)
- Supports compressed files (`.gz`)
- Good for small datasets or custom data

## 🔍 Data Validation

SingleCellStudio automatically checks your data for:
- **File integrity**: Ensures files are readable and complete
- **Dimension consistency**: Verifies cell and gene counts match
- **Data quality**: Identifies empty cells, low-expression genes
- **Format compliance**: Validates 10X format specifications
- **Memory requirements**: Estimates memory usage

## ⚠️ Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "File not found" | Check file paths and permissions |
| "Format not recognized" | Ensure files follow 10X naming conventions |
| "Memory error" | Use H5 format or filter data first |
| "Empty dataset" | Check for compressed files (.gz) |
| "Duplicate gene names" | Will be automatically handled |

## 📊 Example Data Structure

### 10X MTX Folder:
```
filtered_feature_bc_matrix/
├── matrix.mtx.gz      # Expression values
├── barcodes.tsv.gz    # Cell identifiers  
└── features.tsv.gz    # Gene information
```

### CSV Format:
```
genes,CELL1,CELL2,CELL3,...
GENE1,0,5,12,...
GENE2,3,0,8,...
...
```
""")
        tab_widget.addTab(formats_text, "Data Formats")
        
        # Analysis Guide tab
        analysis_text = QTextEdit()
        analysis_text.setReadOnly(True)
        analysis_text.setMarkdown("""
# Analysis Pipeline Guide

## 🔬 QC to Cluster Pipeline

### Quality Control Steps
1. **Calculate QC Metrics**
   - Total UMI counts per cell
   - Number of genes per cell
   - Mitochondrial gene percentage
   - Ribosomal gene percentage

2. **Filter Cells & Genes**
   - Remove low-quality cells (< min genes)
   - Remove rarely expressed genes (< min cells)
   - Filter high mitochondrial content (optional)

3. **Normalization**
   - Total-count normalization to target sum
   - Log transformation (log1p)
   - Preserves raw data for later use

4. **Feature Selection**
   - Identify highly variable genes (HVGs)
   - Typically 2,000-5,000 most variable genes
   - Used for downstream dimensionality reduction

5. **Dimensionality Reduction**
   - Principal Component Analysis (PCA)
   - UMAP for visualization
   - Preserves neighborhood structure

6. **Clustering**
   - Leiden clustering algorithm
   - Resolution parameter controls granularity
   - Higher resolution = more clusters

## 🧬 Cell Type Annotation

### Method Selection
- **Auto**: Recommended for most users
- **Reference-based**: Uses built-in signatures (13+ cell types)
- **Marker-based**: Uses known marker genes
- **CellTypist**: Machine learning models (coming soon)

### Built-in Cell Types
- **Immune cells**: T cells, B cells, NK cells, Monocytes, Macrophages
- **Specialized immune**: CD4+ T, CD8+ T, Regulatory T, Dendritic, Neutrophils
- **Tissue cells**: Endothelial, Fibroblasts, Epithelial
- **Secretory**: Plasma cells

### Custom Marker Genes
```json
{
    "Hepatocytes": ["ALB", "AFP", "APOA1"],
    "Kupffer_cells": ["CD68", "CLEC4F", "VSIG4"],
    "Stellate_cells": ["ACTA2", "COL1A1", "PDGFRB"]
}
```

## 📈 Parameter Guidelines

### QC Parameters
- **Min genes per cell**: 200-500 (filter empty droplets)
- **Min cells per gene**: 3-10 (remove noise genes)
- **Target sum**: 10,000 (standard normalization)

### Analysis Parameters  
- **Variable genes**: 2,000-5,000 (balance detail vs noise)
- **PCA components**: 30-50 (capture main variation)
- **Clustering resolution**: 0.3-1.0 (adjust granularity)

### Annotation Parameters
- **Confidence threshold**: 0.3-0.7 (balance sensitivity vs specificity)
- **Method**: Auto (recommended) or specific method

## 🎯 Best Practices

### Data Preparation
1. Use high-quality, well-prepared single-cell data
2. Remove ambient RNA and doublets if possible
3. Ensure adequate sequencing depth

### Analysis Strategy
1. Start with default parameters
2. Examine clustering results biologically
3. Adjust resolution if needed
4. Validate annotations with known markers

### Quality Assessment
1. Check QC metrics distributions
2. Verify cluster separation in UMAP
3. Examine marker gene expression
4. Validate with literature/prior knowledge
""")
        tab_widget.addTab(analysis_text, "Analysis Guide")
        
        layout.addWidget(tab_widget)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()

    def show_tutorials(self):
        """Show tutorials and workflows"""
        self.show_getting_started()  # For now, redirect to getting started

    def show_user_manual(self):
        """Show comprehensive user manual"""
        dialog = QDialog(self)
        dialog.setWindowTitle("SingleCellStudio User Manual")
        dialog.setMinimumSize(900, 700)
        dialog.resize(1000, 800)
        
        layout = QVBoxLayout()
        
        # Create comprehensive manual content
        manual_text = QTextEdit()
        manual_text.setReadOnly(True)
        manual_text.setMarkdown("""
# SingleCellStudio User Manual

## 📖 Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)  
3. [Data Import](#data-import)
4. [Analysis Pipeline](#analysis-pipeline)
5. [Cell Annotation](#cell-annotation)
6. [Visualization](#visualization)
7. [Export & Results](#export--results)
8. [Troubleshooting](#troubleshooting)

## Introduction

SingleCellStudio is a professional-grade application for single-cell RNA-seq analysis. It provides:
- **Comprehensive pipeline**: From raw data to annotated cell types
- **Professional interface**: Clean, intuitive design for researchers
- **Advanced methods**: State-of-the-art algorithms and visualizations
- **Export capabilities**: Publication-ready plots and processed data

## Installation

### System Requirements
- **Operating System**: Windows 10/11, Linux, macOS
- **Memory**: 8GB RAM minimum, 16GB+ recommended
- **Storage**: 2GB free space for installation
- **Python**: 3.8+ (included in standalone installer)

### Installation Methods
1. **Standalone Installer** (Recommended)
   - Download from official website
   - Run installer and follow prompts
   - No Python knowledge required

2. **Python Package**
   ```bash
   pip install singlecellstudio
   singlecellstudio --gui
   ```

## Data Import

### Supported Formats
See "Data Formats" tab in Getting Started for complete details.

### Import Process
1. Click **"Import Single Cell Data"**
2. Navigate to your data file/folder
3. Review automatic format detection
4. Check data validation results
5. Confirm import to workspace

### Data Validation
- Automatic quality checks
- Format compliance verification
- Memory usage estimation
- Recommendations for optimization

## Analysis Pipeline

### QC to Cluster Workflow
1. **Quality Control**: Calculate metrics, filter cells/genes
2. **Normalization**: Total-count normalize and log-transform
3. **Feature Selection**: Identify highly variable genes
4. **Dimensionality Reduction**: PCA and UMAP
5. **Clustering**: Leiden algorithm for cell grouping

### Parameter Optimization
- Start with defaults for most datasets
- Adjust based on data characteristics
- Use biological knowledge to validate results

## Cell Annotation

### Available Methods
1. **Reference-based**: Automated using built-in signatures
2. **Marker-based**: Uses known marker genes
3. **Auto**: Selects best method automatically

### Custom Annotations
- Define tissue-specific marker genes
- JSON format for custom cell types
- Confidence scoring and validation

## Visualization

### Interactive Plots
- **UMAP**: Colored by cell types, clusters, or metadata
- **Proportions**: Cell type distribution charts
- **Confidence**: Annotation quality metrics
- **QC Metrics**: Data quality visualizations

### Plot Generation
- Real-time parameter adjustment
- Multiple coloring options
- Export to high-resolution formats

## Export & Results

### File Outputs
- **Complete dataset**: `complete_analysis_with_annotation.h5ad`
- **Summary files**: Human-readable analysis summary
- **Visualizations**: High-quality plot images
- **Metadata**: Analysis parameters and results

### Export Options
- **Export Data**: Save annotated AnnData object
- **Export Plots**: Save all visualizations
- **Open Folder**: Access complete results directory

## Troubleshooting

### Common Issues
1. **Memory errors**: Use smaller datasets or increase RAM
2. **Import failures**: Check file format and permissions
3. **Analysis errors**: Verify data quality and parameters
4. **Annotation issues**: Ensure clustering completed successfully

### Getting Help
- Check validation messages for specific guidance
- Review parameter recommendations
- Consult built-in documentation
- Contact support for technical issues

### Performance Tips
- Use H5 format for large datasets
- Filter low-quality data early
- Adjust parameters based on dataset size
- Close other applications to free memory

## Advanced Features

### Batch Processing
- Load and analyze multiple datasets
- Compare results across experiments
- Export combined analyses

### Custom Workflows
- Modify analysis parameters
- Create custom marker gene sets
- Develop tissue-specific protocols

### Integration
- Export to scanpy/Seurat workflows
- Compatible with standard formats
- Seamless data exchange

---

*For additional support, visit our documentation website or contact technical support.*
""")
        
        layout.addWidget(manual_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def show_version_info(self):
        """Show version information"""
        msg = QMessageBox()
        msg.setWindowTitle("Version Information")
        msg.setText(f"SingleCellStudio Professional {VERSION_STRING}")
        msg.setInformativeText(f"""
Professional Single Cell RNA-seq Analysis Software

Version: {VERSION_STRING}
Platform: {sys.platform.capitalize()}
Python: {sys.version.split()[0]}

Analysis Engine: {'Available' if ANALYSIS_AVAILABLE else 'Not Available'}
Visualization: {'Available' if VISUALIZATION_AVAILABLE else 'Not Available'}

Build Date: 2024
License: Commercial
        """)
        msg.exec()
    
    def show_about(self):
        """Show about dialog"""
        msg = QMessageBox()
        msg.setWindowTitle("About SingleCellStudio")
        msg.setText(f"SingleCellStudio Professional {VERSION_STRING}")
        msg.setInformativeText("""
Commercial-Grade Single Cell RNA-seq Analysis Platform

A professional software solution for single cell transcriptome analysis,
designed to rival industry leaders like CLC Workbench.

Key Features:
• Comprehensive analysis pipelines
• Professional user interface
• Publication-quality visualizations
• Advanced statistical methods
• Commercial support

© 2024 SingleCellStudio Inc.
All rights reserved.
        """)
        msg.exec()

    def download_sample_data(self):
        """Download or access sample data for testing"""
        msg = QMessageBox()
        msg.setWindowTitle("Sample Data")
        msg.setText("Sample Data Access")
        msg.setInformativeText("""
Sample datasets are available for testing SingleCellStudio:

📁 Local Sample Data:
• examples/sample_data/ - Small test datasets
• examples/filtered_feature_bc_matrix.h5 - 10X H5 format example

🌐 Online Resources:
• 10X Genomics datasets: support.10xgenomics.com
• PBMC 3K dataset (recommended for testing)
• Various tissue-specific datasets

💡 Quick Start:
1. Navigate to examples/sample_data/ folder
2. Use filtered_feature_bc_matrix.h5 for testing
3. Follow the Getting Started guide

Would you like to open the sample data folder?
        """)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            # Try to open the sample data folder
            sample_dir = Path(__file__).parent.parent.parent / "examples" / "sample_data"
            if sample_dir.exists():
                import subprocess
                import platform
                
                try:
                    if platform.system() == "Windows":
                        subprocess.run(["explorer", str(sample_dir)])
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", str(sample_dir)])
                    else:  # Linux
                        subprocess.run(["xdg-open", str(sample_dir)])
                except Exception as e:
                    QMessageBox.information(
                        self, 
                        "Sample Data Location", 
                        f"Sample data is located at:\n{sample_dir}\n\n"
                        f"Please navigate to this folder manually.\n\n"
                        f"Error opening folder: {e}"
                    )
            else:
                QMessageBox.information(
                    self, 
                    "Sample Data Not Found", 
                    f"Sample data folder not found at expected location:\n{sample_dir}\n\n"
                    "Please check the examples/ directory or download sample data from:\n"
                    "• 10X Genomics website\n"
                    "• SingleCellStudio documentation"
                )

# Main execution function for testing
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create and show the professional main window
    window = ProfessionalMainWindow()
    window.show()
    
    sys.exit(app.exec()) 
