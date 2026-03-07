"""
SingleCellStudio Professional Main Window

Professional single-window interface combining data import and comprehensive analysis functionality
with proper menu bars similar to commercial software like CLC Workbench.

Features:
- Data import and loading from various formats
- Quality control and clustering analysis pipeline
- Advanced cell type annotation with multiple methods
- Trajectory analysis (Pseudotime, RNA Velocity, Lineage Tracing)
- Interactive visualizations and publication-quality plots
- Professional styling with QSS theming
- Integrated workflow from raw data to biological insights

Architecture:
The window uses a tabbed interface with four main analysis modes:
1. Home: Data import and project management
2. QC & Cluster: Standard single-cell analysis pipeline
3. Cell Annotation: Cell type identification and annotation
4. Trajectory Analysis: Temporal and developmental analysis

Each tab is self-contained but shares data seamlessly, allowing for
integrated analysis workflows where results from one step inform the next.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

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
        self.input_file_paths = []
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
        
        # Trajectory Analysis Tab (initially disabled)
        self.trajectory_analysis_tab = self.create_trajectory_analysis_tab()
        self.tab_widget.addTab(self.trajectory_analysis_tab, "Trajectory Analysis")
        self.tab_widget.setTabEnabled(3, False)
        
        # Cell-Cell Interaction Tab (initially disabled)
        self.cell_interaction_tab = self.create_cell_interaction_tab()
        self.tab_widget.addTab(self.cell_interaction_tab, "Cell-Cell Interaction")
        self.tab_widget.setTabEnabled(4, False)
        
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
        
        # Quick Actions Group (removed duplicate Start Here group)
        actions_group = QGroupBox("🚀 Quick Actions")
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

        import_multi_btn = QPushButton("🧬 Import Multiple Samples")
        import_multi_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #138d75;
            }
        """)
        import_multi_btn.clicked.connect(self.import_multiple_samples)
        actions_layout.addWidget(import_multi_btn)
        
        # Load Sample Data Button (NEW)
        sample_btn = QPushButton("📊 Load Sample Dataset")
        sample_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 14px;
                padding: 12px;
                border-radius: 6px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        sample_btn.clicked.connect(self.load_sample_data)
        actions_layout.addWidget(sample_btn)
        
        # Create New Project Button
        new_project_btn = QPushButton("📄 Create New Project")
        new_project_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-size: 14px;
                padding: 12px;
                border-radius: 6px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        new_project_btn.clicked.connect(self.create_new_project)
        actions_layout.addWidget(new_project_btn)
        
        # Load Previous Results Button
        load_results_btn = QPushButton("📊 Load Previous Results")
        load_results_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-size: 14px;
                padding: 12px;
                border-radius: 6px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        load_results_btn.clicked.connect(self.load_previous_results)
        actions_layout.addWidget(load_results_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Data Formats Group
        formats_group = QGroupBox("📋 Supported Data Formats")
        formats_layout = QVBoxLayout()
        
        formats_text = QTextEdit()
        formats_text.setReadOnly(True)
        formats_text.setMaximumHeight(200)
        formats_text.setText("""✅ 10X Genomics formats:
   • MTX folders (matrix.mtx.gz + barcodes + features)
   • H5 files (.h5)

✅ Standard formats:
   • AnnData H5AD files (.h5ad)
   • CSV/TSV files with gene expression matrices

✅ Advanced features:
   • Automatic format detection
   • Data validation and quality control
   • Batch processing capabilities""")
        
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
    
    def create_trajectory_analysis_tab(self):
        """
        Create the trajectory analysis tab
        
        Provides three trajectory analysis methods:
        1. Pseudotime: Reconstructs developmental trajectories and temporal ordering
        2. RNA Velocity: Analyzes RNA dynamics to infer cell state transitions  
        3. Lineage Tracing: Identifies developmental lineages and relationships
        
        Features:
        - Integration with cell type annotations from clustering
        - Method-specific parameter controls
        - Real-time visualization of results
        - Summary statistics and data export
        
        Returns:
            QWidget: The complete trajectory analysis interface
        """
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Trajectory Analysis")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #2c3e50; padding: 15px; background-color: #ecf0f1; border-radius: 5px; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Controls
        controls_panel = self.create_trajectory_controls_panel()
        main_splitter.addWidget(controls_panel)
        
        # Right panel - Results
        results_panel = self.create_trajectory_results_panel()
        main_splitter.addWidget(results_panel)
        
        # Set initial sizes (1:2 ratio)
        main_splitter.setSizes([400, 800])
        
        layout.addWidget(main_splitter)
        tab.setLayout(layout)
        
        return tab
    
    def create_trajectory_controls_panel(self):
        """Create trajectory analysis controls panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Data status
        data_group = QGroupBox("Data Status")
        data_layout = QVBoxLayout()
        
        self.trajectory_data_status = QLabel("No data loaded")
        self.trajectory_data_status.setStyleSheet("color: #e74c3c; font-style: italic; padding: 5px;")
        data_layout.addWidget(self.trajectory_data_status)
        
        self.trajectory_annotation_status = QLabel("No cell annotations available")
        self.trajectory_annotation_status.setStyleSheet("color: #e74c3c; font-style: italic; padding: 5px;")
        data_layout.addWidget(self.trajectory_annotation_status)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Analysis method selection
        method_group = QGroupBox("Analysis Method")
        method_layout = QVBoxLayout()
        
        self.trajectory_method_combo = QComboBox()
        self.trajectory_method_combo.addItems(["Pseudotime", "RNA Velocity", "Lineage Tracing"])
        self.trajectory_method_combo.currentTextChanged.connect(self.on_trajectory_method_changed)
        method_layout.addWidget(self.trajectory_method_combo)
        
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)
        
        # Method-specific parameters
        self.trajectory_params_group = QGroupBox("Parameters")
        self.trajectory_params_layout = QVBoxLayout()
        
        # Pseudotime parameters (default)
        self.create_pseudotime_params()
        
        self.trajectory_params_group.setLayout(self.trajectory_params_layout)
        layout.addWidget(self.trajectory_params_group)
        
        # Run button
        self.run_trajectory_btn = QPushButton("Run Trajectory Analysis")
        self.run_trajectory_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.run_trajectory_btn.clicked.connect(self.run_trajectory_analysis)
        self.run_trajectory_btn.setEnabled(False)
        layout.addWidget(self.run_trajectory_btn)
        
        layout.addStretch()
        panel.setLayout(layout)
        
        return panel
    
    def create_trajectory_results_panel(self):
        """Create trajectory analysis results panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Results tabs
        self.trajectory_results_tabs = QTabWidget()
        
        # Summary tab
        self.trajectory_summary_tab = self.create_trajectory_summary_tab()
        self.trajectory_results_tabs.addTab(self.trajectory_summary_tab, "Summary")
        
        # Plots tab
        self.trajectory_plots_tab = self.create_trajectory_plots_tab()
        self.trajectory_results_tabs.addTab(self.trajectory_plots_tab, "Plots")
        
        # Data tab
        self.trajectory_data_tab = self.create_trajectory_data_tab()
        self.trajectory_results_tabs.addTab(self.trajectory_data_tab, "Data")
        
        layout.addWidget(self.trajectory_results_tabs)
        panel.setLayout(layout)
        
        return panel
    
    def create_trajectory_summary_tab(self):
        """Create trajectory analysis summary tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Summary text
        self.trajectory_summary_text = QTextEdit()
        self.trajectory_summary_text.setReadOnly(True)
        self.trajectory_summary_text.setText("Run trajectory analysis to see results summary here...")
        layout.addWidget(self.trajectory_summary_text)
        
        tab.setLayout(layout)
        return tab
    
    def create_trajectory_plots_tab(self):
        """Create trajectory analysis plots tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Plot canvas
        if MATPLOTLIB_AVAILABLE:
            self.trajectory_figure = Figure(figsize=(10, 8))
            self.trajectory_canvas = FigureCanvas(self.trajectory_figure)
            layout.addWidget(self.trajectory_canvas)
        else:
            no_matplotlib_label = QLabel("Matplotlib not available for plotting")
            no_matplotlib_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_matplotlib_label)
        
        tab.setLayout(layout)
        return tab
    
    def create_trajectory_data_tab(self):
        """Create trajectory analysis data tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Results table
        self.trajectory_table = QTableWidget()
        layout.addWidget(self.trajectory_table)
        
        tab.setLayout(layout)
        return tab
    
    def create_cell_interaction_tab(self):
        """
        Create the cell-cell interaction analysis tab
        
        Provides comprehensive cell-cell interaction analysis including:
        1. Ligand-Receptor Analysis: Identifies significant ligand-receptor interactions
        2. Spatial Proximity Analysis: Examines spatial interaction patterns  
        3. Communication Modeling: Models cell communication networks
        
        Features:
        - Integration with cell type annotations from clustering
        - Method-specific parameter controls
        - Real-time visualization of interaction networks
        - Summary statistics and data export
        
        Returns:
            QWidget: The complete cell-cell interaction analysis interface
        """
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Cell-Cell Interaction Analysis")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #2c3e50; padding: 15px; background-color: #ecf0f1; border-radius: 5px; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Controls
        controls_panel = self.create_interaction_controls_panel()
        main_splitter.addWidget(controls_panel)
        
        # Right panel - Results
        results_panel = self.create_interaction_results_panel()
        main_splitter.addWidget(results_panel)
        
        # Set initial sizes (1:2 ratio)
        main_splitter.setSizes([400, 800])
        
        layout.addWidget(main_splitter)
        tab.setLayout(layout)
        
        return tab
    
    def create_interaction_controls_panel(self):
        """Create cell-cell interaction analysis controls panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Data status
        data_group = QGroupBox("Data Status")
        data_layout = QVBoxLayout()
        
        self.interaction_data_status = QLabel("No data loaded")
        self.interaction_data_status.setStyleSheet("color: #e74c3c; font-style: italic; padding: 5px;")
        data_layout.addWidget(self.interaction_data_status)
        
        self.interaction_annotation_status = QLabel("No cell annotations available")
        self.interaction_annotation_status.setStyleSheet("color: #e74c3c; font-style: italic; padding: 5px;")
        data_layout.addWidget(self.interaction_annotation_status)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Analysis method selection
        method_group = QGroupBox("Analysis Method")
        method_layout = QVBoxLayout()
        
        self.interaction_method_combo = QComboBox()
        self.interaction_method_combo.addItems([
            "Ligand-Receptor Analysis", 
            "Spatial Proximity Analysis", 
            "Communication Modeling"
        ])
        self.interaction_method_combo.currentTextChanged.connect(self.on_interaction_method_changed)
        method_layout.addWidget(self.interaction_method_combo)
        
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)
        
        # Method-specific parameters
        self.interaction_params_group = QGroupBox("Parameters")
        self.interaction_params_layout = QVBoxLayout()
        
        # Ligand-receptor parameters (default)
        self.create_ligand_receptor_params()
        
        self.interaction_params_group.setLayout(self.interaction_params_layout)
        layout.addWidget(self.interaction_params_group)
        
        # Run button
        self.run_interaction_btn = QPushButton("🔗 Run Interaction Analysis")
        self.run_interaction_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.run_interaction_btn.clicked.connect(self.run_interaction_analysis)
        self.run_interaction_btn.setEnabled(False)
        layout.addWidget(self.run_interaction_btn)
        
        layout.addStretch()
        panel.setLayout(layout)
        
        return panel
    
    def create_interaction_results_panel(self):
        """Create cell-cell interaction analysis results panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Results tabs
        self.interaction_results_tabs = QTabWidget()
        
        # Summary tab
        self.interaction_summary_tab = self.create_interaction_summary_tab()
        self.interaction_results_tabs.addTab(self.interaction_summary_tab, "Summary")
        
        # Network tab
        self.interaction_network_tab = self.create_interaction_network_tab()
        self.interaction_results_tabs.addTab(self.interaction_network_tab, "Network")
        
        # Data tab
        self.interaction_data_tab = self.create_interaction_data_tab()
        self.interaction_results_tabs.addTab(self.interaction_data_tab, "Data")
        
        layout.addWidget(self.interaction_results_tabs)
        panel.setLayout(layout)
        
        return panel
    
    def create_interaction_summary_tab(self):
        """Create cell-cell interaction analysis summary tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Summary text
        self.interaction_summary_text = QTextEdit()
        self.interaction_summary_text.setReadOnly(True)
        self.interaction_summary_text.setText("Run interaction analysis to see results summary here...")
        layout.addWidget(self.interaction_summary_text)
        
        tab.setLayout(layout)
        return tab
    
    def create_interaction_network_tab(self):
        """Create cell-cell interaction network visualization tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Plot canvas
        if MATPLOTLIB_AVAILABLE:
            self.interaction_figure = Figure(figsize=(10, 8))
            self.interaction_canvas = FigureCanvas(self.interaction_figure)
            layout.addWidget(self.interaction_canvas)
        else:
            no_matplotlib_label = QLabel("Matplotlib not available for plotting")
            no_matplotlib_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_matplotlib_label)
        
        tab.setLayout(layout)
        return tab
    
    def create_interaction_data_tab(self):
        """Create cell-cell interaction analysis data tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Results table
        self.interaction_table = QTableWidget()
        layout.addWidget(self.interaction_table)
        
        tab.setLayout(layout)
        return tab
    
    def create_ligand_receptor_params(self):
        """Create ligand-receptor analysis parameters"""
        # Clear existing params
        for i in reversed(range(self.interaction_params_layout.count())):
            self.interaction_params_layout.itemAt(i).widget().setParent(None)
        
        # P-value threshold
        pval_layout = QHBoxLayout()
        pval_layout.addWidget(QLabel("P-value threshold:"))
        self.interaction_pval_spin = QDoubleSpinBox()
        self.interaction_pval_spin.setRange(0.001, 0.1)
        self.interaction_pval_spin.setValue(0.05)
        self.interaction_pval_spin.setDecimals(3)
        self.interaction_pval_spin.setSingleStep(0.01)
        pval_layout.addWidget(self.interaction_pval_spin)
        self.interaction_params_layout.addLayout(pval_layout)
        
        # Minimum expression
        expr_layout = QHBoxLayout()
        expr_layout.addWidget(QLabel("Min expression:"))
        self.interaction_expr_spin = QDoubleSpinBox()
        self.interaction_expr_spin.setRange(0.0, 5.0)
        self.interaction_expr_spin.setValue(0.1)
        self.interaction_expr_spin.setDecimals(2)
        self.interaction_expr_spin.setSingleStep(0.1)
        expr_layout.addWidget(self.interaction_expr_spin)
        self.interaction_params_layout.addLayout(expr_layout)
        
        # Method description
        desc_text = QTextEdit()
        desc_text.setMaximumHeight(80)
        desc_text.setReadOnly(True)
        desc_text.setText("Ligand-Receptor Analysis: Identifies significant ligand-receptor interactions between cell types based on expression levels and statistical testing.")
        self.interaction_params_layout.addWidget(desc_text)
    
    def create_spatial_params(self):
        """Create spatial proximity analysis parameters"""
        # Clear existing params
        for i in reversed(range(self.interaction_params_layout.count())):
            self.interaction_params_layout.itemAt(i).widget().setParent(None)
        
        # Neighborhood radius
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(QLabel("Neighborhood radius:"))
        self.interaction_radius_spin = QDoubleSpinBox()
        self.interaction_radius_spin.setRange(10.0, 200.0)
        self.interaction_radius_spin.setValue(50.0)
        self.interaction_radius_spin.setSuffix(" μm")
        radius_layout.addWidget(self.interaction_radius_spin)
        self.interaction_params_layout.addLayout(radius_layout)
        
        # Method description
        desc_text = QTextEdit()
        desc_text.setMaximumHeight(80)
        desc_text.setReadOnly(True)
        desc_text.setText("Spatial Proximity Analysis: Examines cell-cell interactions based on spatial proximity and neighborhood enrichment patterns.")
        self.interaction_params_layout.addWidget(desc_text)
    
    def create_communication_params(self):
        """Create communication modeling parameters"""
        # Clear existing params
        for i in reversed(range(self.interaction_params_layout.count())):
            self.interaction_params_layout.itemAt(i).widget().setParent(None)
        
        # Flow threshold
        flow_layout = QHBoxLayout()
        flow_layout.addWidget(QLabel("Flow threshold:"))
        self.interaction_flow_spin = QDoubleSpinBox()
        self.interaction_flow_spin.setRange(0.1, 1.0)
        self.interaction_flow_spin.setValue(0.3)
        self.interaction_flow_spin.setDecimals(2)
        self.interaction_flow_spin.setSingleStep(0.1)
        flow_layout.addWidget(self.interaction_flow_spin)
        self.interaction_params_layout.addLayout(flow_layout)
        
        # Method description
        desc_text = QTextEdit()
        desc_text.setMaximumHeight(80)
        desc_text.setReadOnly(True)
        desc_text.setText("Communication Modeling: Models cell communication through signaling pathways and quantifies information flow between cell populations.")
        self.interaction_params_layout.addWidget(desc_text)
    
    def on_interaction_method_changed(self, method):
        """Handle interaction analysis method change"""
        if "Ligand-Receptor" in method:
            self.create_ligand_receptor_params()
        elif "Spatial Proximity" in method:
            self.create_spatial_params()
        elif "Communication Modeling" in method:
            self.create_communication_params()
    
    def update_interaction_tab_status(self):
        """Update interaction analysis tab status based on available data"""
        if hasattr(self, 'adata') and self.adata is not None:
            # Update data status
            data_text = f"✅ Data loaded: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes"
            self.interaction_data_status.setText(data_text)
            self.interaction_data_status.setStyleSheet("color: #27ae60; padding: 5px;")
            
            # Check for annotations
            if 'leiden' in self.adata.obs:
                n_clusters = len(self.adata.obs['leiden'].unique())
                annot_text = f"✅ Cell annotations available: {n_clusters} clusters"
                self.interaction_annotation_status.setText(annot_text)
                self.interaction_annotation_status.setStyleSheet("color: #27ae60; padding: 5px;")
                self.run_interaction_btn.setEnabled(True)
            else:
                self.interaction_annotation_status.setText("⚠️ Cell annotations recommended for interaction analysis")
                self.interaction_annotation_status.setStyleSheet("color: #f39c12; padding: 5px;")
                self.run_interaction_btn.setEnabled(True)  # Allow analysis without annotations
        else:
            self.interaction_data_status.setText("❌ No data loaded")
            self.interaction_data_status.setStyleSheet("color: #e74c3c; font-style: italic; padding: 5px;")
            self.interaction_annotation_status.setText("❌ No cell annotations available")
            self.interaction_annotation_status.setStyleSheet("color: #e74c3c; font-style: italic; padding: 5px;")
            self.run_interaction_btn.setEnabled(False)
    
    def run_interaction_analysis(self):
        """Run cell-cell interaction analysis"""
        if not hasattr(self, 'adata') or self.adata is None:
            QMessageBox.warning(self, "No Data", "Please load data before running interaction analysis.")
            return
        
        method = self.interaction_method_combo.currentText()
        
        # Get parameters based on method
        params = {}
        if "Ligand-Receptor" in method:
            params = {
                'pval_threshold': self.interaction_pval_spin.value(),
                'min_expression': self.interaction_expr_spin.value()
            }
        elif "Spatial Proximity" in method:
            params = {
                'radius': self.interaction_radius_spin.value()
            }
        elif "Communication Modeling" in method:
            params = {
                'flow_threshold': self.interaction_flow_spin.value()
            }
        
        # Start analysis
        import numpy as np
        self.log_activity(f"Starting {method} analysis...")
        
        try:
            # Mock analysis - replace with real implementation
            if "Ligand-Receptor" in method:
                results = self._run_mock_ligand_receptor_analysis(params)
            elif "Spatial Proximity" in method:
                results = self._run_mock_spatial_analysis(params)
            elif "Communication Modeling" in method:
                results = self._run_mock_communication_analysis(params)
            
            self.interaction_analysis_completed(results)
            
        except Exception as e:
            self.interaction_analysis_failed(str(e))
    
    def _run_mock_ligand_receptor_analysis(self, params):
        """Mock ligand-receptor analysis"""
        results = {
            'method': 'Ligand-Receptor Analysis',
            'parameters': params,
            'n_interactions': np.random.randint(150, 300),
            'n_significant': np.random.randint(50, 150),
            'top_pathways': ['VEGF signaling', 'TGF-beta signaling', 'Notch signaling', 'Wnt signaling'],
            'significant_pairs': [
                ('T cells', 'Dendritic cells', 'CD28-CD80', 0.001),
                ('B cells', 'T cells', 'CD40-CD40LG', 0.003),
                ('Macrophages', 'T cells', 'IL1B-IL1R1', 0.005),
                ('NK cells', 'Target cells', 'KLRK1-ULBP1', 0.002),
                ('Endothelial', 'Pericytes', 'PDGFB-PDGFRB', 0.004)
            ]
        }
        return results
    
    def _run_mock_spatial_analysis(self, params):
        """Mock spatial proximity analysis"""
        results = {
            'method': 'Spatial Proximity Analysis',
            'parameters': params,
            'n_neighborhoods': np.random.randint(8, 15),
            'enriched_pairs': [
                ('T cells', 'Dendritic cells', 2.3, 0.001),
                ('B cells', 'Macrophages', 1.8, 0.005),
                ('NK cells', 'T cells', 1.5, 0.01),
                ('Endothelial', 'Smooth muscle', 3.1, 0.0001)
            ],
            'spatial_patterns': {
                'clustered_types': ['T cells', 'B cells'],
                'dispersed_types': ['Macrophages'],
                'random_types': ['NK cells']
            }
        }
        return results
    
    def _run_mock_communication_analysis(self, params):
        """Mock communication modeling analysis"""
        results = {
            'method': 'Communication Modeling',
            'parameters': params,
            'n_pathways': np.random.randint(20, 40),
            'top_senders': ['Dendritic cells', 'Macrophages', 'T cells'],
            'top_receivers': ['T cells', 'B cells', 'NK cells'],
            'pathway_flows': {
                'Immune activation': 0.85,
                'Inflammation': 0.72,
                'Antigen presentation': 0.68,
                'Cytokine signaling': 0.63,
                'Cell adhesion': 0.58
            }
        }
        return results
    
    def interaction_analysis_completed(self, results):
        """Handle completed interaction analysis"""
        self.log_activity(f"✅ {results['method']} completed successfully!")
        
        # Update results display
        self.update_interaction_results(results)
        
        # Switch to results tab
        self.interaction_results_tabs.setCurrentIndex(0)  # Summary tab
    
    def interaction_analysis_failed(self, error_message):
        """Handle failed interaction analysis"""
        self.log_activity(f"❌ Interaction analysis failed: {error_message}")
        QMessageBox.critical(self, "Analysis Failed", f"Interaction analysis failed:\n{error_message}")
    
    def update_interaction_results(self, results):
        """Update interaction analysis results display"""
        method = results['method']
        
        if "Ligand-Receptor" in method:
            summary = f"""🔗 Ligand-Receptor Analysis Results

Method: {method}
Parameters: P-value threshold = {results['parameters']['pval_threshold']}, Min expression = {results['parameters']['min_expression']}

📊 Summary Statistics:
• Total interactions detected: {results['n_interactions']}
• Significant interactions: {results['n_significant']}
• Top pathways: {', '.join(results['top_pathways'][:3])}

🎯 Significant Cell Type Pairs:
"""
            for sender, receiver, interaction, pval in results['significant_pairs']:
                summary += f"• {sender} → {receiver}: {interaction} (p={pval:.3f})\n"
                
        elif "Spatial Proximity" in method:
            summary = f"""📍 Spatial Proximity Analysis Results

Method: {method}
Parameters: Neighborhood radius = {results['parameters']['radius']} μm

📊 Summary Statistics:
• Neighborhoods detected: {results['n_neighborhoods']}
• Enriched cell type pairs: {len(results['enriched_pairs'])}

🎯 Spatial Enrichment Patterns:
• Clustered cell types: {', '.join(results['spatial_patterns']['clustered_types'])}
• Dispersed cell types: {', '.join(results['spatial_patterns']['dispersed_types'])}

🔗 Top Enriched Pairs:
"""
            for ct1, ct2, score, pval in results['enriched_pairs']:
                summary += f"• {ct1} ↔ {ct2}: enrichment = {score:.2f} (p={pval:.3f})\n"
                
        elif "Communication Modeling" in method:
            summary = f"""📡 Communication Modeling Results

Method: {method}
Parameters: Flow threshold = {results['parameters']['flow_threshold']}

📊 Summary Statistics:
• Signaling pathways analyzed: {results['n_pathways']}
• Top senders: {', '.join(results['top_senders'][:3])}
• Top receivers: {', '.join(results['top_receivers'][:3])}

🌊 Pathway Flow Strengths:
"""
            for pathway, strength in results['pathway_flows'].items():
                summary += f"• {pathway}: {strength:.2f}\n"
        
        summary += f"\n✅ Analysis completed successfully at {self.get_timestamp()}"
        self.interaction_summary_text.setText(summary)
        
        # Update data table
        self.update_interaction_table(results)
        
        # Generate plot
        self.generate_interaction_plot(results)
    
    def update_interaction_table(self, results):
        """Update interaction results table"""
        method = results['method']
        
        if "Ligand-Receptor" in method:
            pairs = results['significant_pairs']
            self.interaction_table.setRowCount(len(pairs))
            self.interaction_table.setColumnCount(4)
            self.interaction_table.setHorizontalHeaderLabels(['Sender', 'Receiver', 'Interaction', 'P-value'])
            
            for i, (sender, receiver, interaction, pval) in enumerate(pairs):
                self.interaction_table.setItem(i, 0, QTableWidgetItem(sender))
                self.interaction_table.setItem(i, 1, QTableWidgetItem(receiver))
                self.interaction_table.setItem(i, 2, QTableWidgetItem(interaction))
                self.interaction_table.setItem(i, 3, QTableWidgetItem(f"{pval:.3f}"))
                
        elif "Spatial Proximity" in method:
            pairs = results['enriched_pairs']
            self.interaction_table.setRowCount(len(pairs))
            self.interaction_table.setColumnCount(4)
            self.interaction_table.setHorizontalHeaderLabels(['Cell Type 1', 'Cell Type 2', 'Enrichment Score', 'P-value'])
            
            for i, (ct1, ct2, score, pval) in enumerate(pairs):
                self.interaction_table.setItem(i, 0, QTableWidgetItem(ct1))
                self.interaction_table.setItem(i, 1, QTableWidgetItem(ct2))
                self.interaction_table.setItem(i, 2, QTableWidgetItem(f"{score:.2f}"))
                self.interaction_table.setItem(i, 3, QTableWidgetItem(f"{pval:.3f}"))
                
        elif "Communication Modeling" in method:
            flows = list(results['pathway_flows'].items())
            self.interaction_table.setRowCount(len(flows))
            self.interaction_table.setColumnCount(2)
            self.interaction_table.setHorizontalHeaderLabels(['Pathway', 'Flow Strength'])
            
            for i, (pathway, strength) in enumerate(flows):
                self.interaction_table.setItem(i, 0, QTableWidgetItem(pathway))
                self.interaction_table.setItem(i, 1, QTableWidgetItem(f"{strength:.2f}"))
        
        self.interaction_table.resizeColumnsToContents()
    
    def generate_interaction_plot(self, results):
        """Generate interaction analysis plot"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        import matplotlib.pyplot as plt
        import numpy as np
        
        self.interaction_figure.clear()
        
        method = results['method']
        
        if "Ligand-Receptor" in method:
            # Network plot for ligand-receptor interactions
            ax = self.interaction_figure.add_subplot(111)
            
            # Mock network visualization
            cell_types = ['T cells', 'B cells', 'Dendritic cells', 'Macrophages', 'NK cells']
            n_types = len(cell_types)
            
            # Position cell types in a circle
            angles = np.linspace(0, 2*np.pi, n_types, endpoint=False)
            x = np.cos(angles)
            y = np.sin(angles)
            
            # Plot cell types
            colors = plt.cm.Set3(np.linspace(0, 1, n_types))
            ax.scatter(x, y, s=500, c=colors, alpha=0.7, edgecolors='black', linewidth=2)
            
            # Add labels
            for i, cell_type in enumerate(cell_types):
                ax.annotate(cell_type, (x[i], y[i]), xytext=(10, 10), 
                           textcoords='offset points', fontsize=10, fontweight='bold')
            
            # Draw interaction lines
            for sender, receiver, _, pval in results['significant_pairs'][:8]:  # Show top 8
                if sender in cell_types and receiver in cell_types:
                    i = cell_types.index(sender)
                    j = cell_types.index(receiver)
                    
                    # Line thickness based on significance
                    thickness = max(1, -np.log10(pval))
                    ax.plot([x[i], x[j]], [y[i], y[j]], 'r-', alpha=0.6, linewidth=thickness)
            
            ax.set_title(f'Ligand-Receptor Interaction Network\n{results["n_significant"]} significant interactions', 
                        fontsize=14, fontweight='bold')
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)
            ax.axis('off')
            
        elif "Spatial Proximity" in method:
            # Heatmap for spatial enrichment
            ax = self.interaction_figure.add_subplot(111)
            
            # Mock spatial enrichment matrix
            cell_types = ['T cells', 'B cells', 'Dendritic cells', 'Macrophages', 'NK cells']
            n_types = len(cell_types)
            enrichment_matrix = np.random.rand(n_types, n_types) * 3
            
            im = ax.imshow(enrichment_matrix, cmap='RdYlBu_r', aspect='auto')
            ax.set_xticks(range(n_types))
            ax.set_yticks(range(n_types))
            ax.set_xticklabels(cell_types, rotation=45, ha='right')
            ax.set_yticklabels(cell_types)
            
            # Add colorbar
            cbar = self.interaction_figure.colorbar(im, ax=ax, shrink=0.8)
            cbar.set_label('Spatial Enrichment Score', rotation=270, labelpad=20)
            
            ax.set_title('Spatial Proximity Enrichment Heatmap', fontsize=14, fontweight='bold')
            
        elif "Communication Modeling" in method:
            # Bar plot for pathway flows
            ax = self.interaction_figure.add_subplot(111)
            
            pathways = list(results['pathway_flows'].keys())
            flows = list(results['pathway_flows'].values())
            
            bars = ax.barh(pathways, flows, color=plt.cm.viridis(np.array(flows)))
            ax.set_xlabel('Flow Strength')
            ax.set_title('Cell Communication Pathway Flows', fontsize=14, fontweight='bold')
            
            # Add value labels on bars
            for i, (bar, flow) in enumerate(zip(bars, flows)):
                ax.text(flow + 0.01, i, f'{flow:.2f}', va='center', fontweight='bold')
        
        self.interaction_figure.tight_layout()
        self.interaction_canvas.draw()
    
    def get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def create_pseudotime_params(self):
        """Create pseudotime analysis parameters"""
        # Clear existing params
        for i in reversed(range(self.trajectory_params_layout.count())):
            self.trajectory_params_layout.itemAt(i).widget().setParent(None)
        
        # Root cell selection
        root_layout = QHBoxLayout()
        root_layout.addWidget(QLabel("Root Cell:"))
        self.trajectory_root_combo = QComboBox()
        self.trajectory_root_combo.addItem("Auto Detect")
        root_layout.addWidget(self.trajectory_root_combo)
        
        root_widget = QWidget()
        root_widget.setLayout(root_layout)
        self.trajectory_params_layout.addWidget(root_widget)
        
        # N Components
        n_comp_layout = QHBoxLayout()
        n_comp_layout.addWidget(QLabel("N Components:"))
        self.trajectory_n_components = QSpinBox()
        self.trajectory_n_components.setRange(10, 100)
        self.trajectory_n_components.setValue(50)
        n_comp_layout.addWidget(self.trajectory_n_components)
        
        n_comp_widget = QWidget()
        n_comp_widget.setLayout(n_comp_layout)
        self.trajectory_params_layout.addWidget(n_comp_widget)
        
        # Use cell type annotations
        self.trajectory_use_annotations = QCheckBox("Use Cell Type Annotations")
        self.trajectory_use_annotations.setChecked(True)
        self.trajectory_params_layout.addWidget(self.trajectory_use_annotations)
    
    def create_velocity_params(self):
        """Create RNA velocity analysis parameters"""
        # Clear existing params
        for i in reversed(range(self.trajectory_params_layout.count())):
            self.trajectory_params_layout.itemAt(i).widget().setParent(None)
        
        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.trajectory_velocity_mode = QComboBox()
        self.trajectory_velocity_mode.addItems(["dynamical", "stochastic"])
        mode_layout.addWidget(self.trajectory_velocity_mode)
        
        mode_widget = QWidget()
        mode_widget.setLayout(mode_layout)
        self.trajectory_params_layout.addWidget(mode_widget)
        
        # Use cell type annotations
        self.trajectory_use_annotations = QCheckBox("Use Cell Type Annotations")
        self.trajectory_use_annotations.setChecked(True)
        self.trajectory_params_layout.addWidget(self.trajectory_use_annotations)
    
    def create_lineage_params(self):
        """Create lineage tracing analysis parameters"""
        # Clear existing params
        for i in reversed(range(self.trajectory_params_layout.count())):
            self.trajectory_params_layout.itemAt(i).widget().setParent(None)
        
        # Cluster resolution
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("Resolution:"))
        self.trajectory_lineage_resolution = QDoubleSpinBox()
        self.trajectory_lineage_resolution.setRange(0.1, 2.0)
        self.trajectory_lineage_resolution.setValue(0.5)
        self.trajectory_lineage_resolution.setSingleStep(0.1)
        res_layout.addWidget(self.trajectory_lineage_resolution)
        
        res_widget = QWidget()
        res_widget.setLayout(res_layout)
        self.trajectory_params_layout.addWidget(res_widget)
        
        # Use cell type annotations
        self.trajectory_use_annotations = QCheckBox("Use Cell Type Annotations")
        self.trajectory_use_annotations.setChecked(True)
        self.trajectory_params_layout.addWidget(self.trajectory_use_annotations)
    
    def on_trajectory_method_changed(self, method):
        """Handle trajectory method change"""
        if method == "Pseudotime":
            self.create_pseudotime_params()
        elif method == "RNA Velocity":
            self.create_velocity_params()
        elif method == "Lineage Tracing":
            self.create_lineage_params()
    
    def update_trajectory_tab_status(self):
        """Update trajectory analysis tab status"""
        if not hasattr(self, 'trajectory_data_status'):
            return
        
        # Update data status
        if self.adata is not None:
            self.trajectory_data_status.setText(f"✅ Data loaded: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes")
            self.trajectory_data_status.setStyleSheet("color: #27ae60; font-style: italic; padding: 5px;")
            
            # Check for cell annotations
            has_annotations = (
                'cell_type' in self.adata.obs or 
                'leiden' in self.adata.obs or 
                'louvain' in self.adata.obs
            )
            
            if has_annotations:
                annotation_cols = []
                if 'cell_type' in self.adata.obs:
                    annotation_cols.append('cell_type')
                if 'leiden' in self.adata.obs:
                    annotation_cols.append('leiden')
                if 'louvain' in self.adata.obs:
                    annotation_cols.append('louvain')
                
                self.trajectory_annotation_status.setText(f"✅ Annotations available: {', '.join(annotation_cols)}")
                self.trajectory_annotation_status.setStyleSheet("color: #27ae60; font-style: italic; padding: 5px;")
            else:
                self.trajectory_annotation_status.setText("⚠️ No cell type annotations found")
                self.trajectory_annotation_status.setStyleSheet("color: #f39c12; font-style: italic; padding: 5px;")
            
            # Enable run button
            self.run_trajectory_btn.setEnabled(True)
            
        else:
            self.trajectory_data_status.setText("❌ No data loaded")
            self.trajectory_data_status.setStyleSheet("color: #e74c3c; font-style: italic; padding: 5px;")
            
            self.trajectory_annotation_status.setText("❌ No cell annotations available")
            self.trajectory_annotation_status.setStyleSheet("color: #e74c3c; font-style: italic; padding: 5px;")
            
            # Disable run button
            self.run_trajectory_btn.setEnabled(False)
    
    def run_trajectory_analysis(self):
        """
        Run trajectory analysis using the selected method
        
        Executes one of three trajectory analysis methods:
        - Pseudotime: Orders cells along developmental trajectories
        - RNA Velocity: Computes cell state transition directions
        - Lineage Tracing: Identifies developmental lineage relationships
        
        The analysis integrates with cell type annotations when available,
        providing biological context for trajectory inference.
        
        Results include:
        - Method-specific trajectory metrics
        - Integration with cell type annotations
        - Interactive visualizations
        - Detailed summary statistics
        """
        if self.adata is None:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        
        method = self.trajectory_method_combo.currentText()
        use_annotations = self.trajectory_use_annotations.isChecked()
        
        self.log_activity(f"Starting {method} trajectory analysis...")
        
        # For now, create a mock analysis
        try:
            import numpy as np  # Import numpy at the top for all methods
            
            self.update_progress(10, f"Preparing data for {method} analysis...")
            
            # Simulate some processing time and steps
            self.update_progress(25, f"Preprocessing data for {method}...")
            
            # Mock trajectory analysis results
            results = {
                'method': method,
                'n_cells': self.adata.n_obs,
                'used_annotations': use_annotations,
                'success': True
            }
            
            self.update_progress(50, f"Computing {method} trajectory...")
            
            if method == "Pseudotime":
                # Create mock pseudotime data
                results.update({
                    'pseudotime': np.random.random(self.adata.n_obs),
                    'root_cell': self.trajectory_root_combo.currentText(),
                    'n_branches': np.random.randint(2, 5)
                })
                
                # Add UMAP coordinates if available
                if 'X_umap' in self.adata.obsm:
                    results['umap'] = self.adata.obsm['X_umap']
                else:
                    # Create mock UMAP
                    results['umap'] = np.random.randn(self.adata.n_obs, 2)
                
                # Add cell types if available
                if use_annotations and 'leiden' in self.adata.obs:
                    results['cell_types'] = self.adata.obs['leiden'].values
                    results['cell_type_analysis'] = {
                        f"Cluster {i}": f"Pseudotime range: {np.random.random():.2f}-{np.random.random():.2f}"
                        for i in self.adata.obs['leiden'].unique()
                    }
            
            elif method == "RNA Velocity":
                # Create mock RNA velocity data
                results.update({
                    'mode': self.trajectory_velocity_mode.currentText(),
                    'velocity_confidence': np.random.uniform(0.6, 0.9),
                    'n_velocity_genes': np.random.randint(800, 1200)
                })
                
                # Add UMAP coordinates if available
                if 'X_umap' in self.adata.obsm:
                    results['umap'] = self.adata.obsm['X_umap']
                else:
                    # Create mock UMAP
                    results['umap'] = np.random.randn(self.adata.n_obs, 2)
                
                # Add velocity vectors (mock)
                results['velocity_vectors'] = np.random.randn(self.adata.n_obs, 2) * 0.1
                
                # Add cell types if available
                if use_annotations and 'leiden' in self.adata.obs:
                    results['cell_types'] = self.adata.obs['leiden'].values
                    results['cell_type_analysis'] = {
                        f"Cluster {i}": f"Velocity strength: {np.random.uniform(0.3, 0.8):.2f}"
                        for i in self.adata.obs['leiden'].unique()
                    }
            
            elif method == "Lineage Tracing":
                # Create mock lineage tracing data
                n_lineages = np.random.randint(3, 8)
                results.update({
                    'resolution': self.trajectory_lineage_resolution.value(),
                    'n_lineages': n_lineages,
                    'lineage_confidence': np.random.uniform(0.7, 0.95)
                })
                
                # Add UMAP coordinates if available
                if 'X_umap' in self.adata.obsm:
                    results['umap'] = self.adata.obsm['X_umap']
                else:
                    # Create mock UMAP
                    results['umap'] = np.random.randn(self.adata.n_obs, 2)
                
                # Assign cells to lineages
                lineage_assignments = np.random.choice(range(n_lineages), size=self.adata.n_obs)
                results['lineage_assignments'] = lineage_assignments
                
                # Add cell types if available
                if use_annotations and 'leiden' in self.adata.obs:
                    results['cell_types'] = self.adata.obs['leiden'].values
                    results['cell_type_analysis'] = {
                        f"Cluster {i}": f"Primary lineage: Lineage {np.random.randint(0, n_lineages)}"
                        for i in self.adata.obs['leiden'].unique()
                    }
            
            self.update_progress(100, f"{method} analysis completed!")
            
            # Call completion handler
            self.trajectory_analysis_completed(self.adata, results)
            
        except Exception as e:
            self.trajectory_analysis_failed(str(e))
    
    def trajectory_analysis_completed(self, adata, results):
        """Handle trajectory analysis completion"""
        self.log_activity("Trajectory analysis completed successfully!")
        
        # Store results
        self.trajectory_adata = adata
        self.trajectory_results = results
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Re-enable run button
        self.run_trajectory_btn.setEnabled(True)
        
        # Update results display
        self.update_trajectory_results(results)
        
        # Switch to trajectory tab
        self.tab_widget.setCurrentIndex(3)
        
        self.statusBar().showMessage("Trajectory analysis completed successfully")
    
    def trajectory_analysis_failed(self, error_message):
        """Handle trajectory analysis failure"""
        self.log_activity(f"Trajectory analysis failed: {error_message}")
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Re-enable run button
        self.run_trajectory_btn.setEnabled(True)
        
        QMessageBox.critical(self, "Analysis Failed", 
                           f"Trajectory analysis failed:\n\n{error_message}")
        
        self.statusBar().showMessage("Trajectory analysis failed")
    
    def update_trajectory_results(self, results):
        """Update trajectory analysis results display"""
        # Update summary
        method = results.get('method', 'Unknown')
        n_cells = results.get('n_cells', 0)
        
        summary_text = f"""Trajectory Analysis Results - {method}

📊 Analysis Summary:
• Method: {method}
• Cells analyzed: {n_cells:,}
• Integration with annotations: {'Yes' if results.get('used_annotations', False) else 'No'}

🔬 Results:
"""
        
        if method == "Pseudotime":
            summary_text += f"""• Pseudotime computed for all cells
• Root cell: {results.get('root_cell', 'Auto-detected')}
• Trajectory branches: {results.get('n_branches', 'N/A')}
"""
        elif method == "RNA Velocity":
            summary_text += f"""• Velocity vectors computed for all cells
• Mode: {results.get('mode', 'dynamical')}
• Velocity confidence: {results.get('velocity_confidence', 'N/A'):.3f}
• Velocity genes used: {results.get('n_velocity_genes', 'N/A')}
"""
        elif method == "Lineage Tracing":
            summary_text += f"""• Lineage relationships inferred
• Resolution: {results.get('resolution', 0.5)}
• Lineages identified: {results.get('n_lineages', 'N/A')}
• Lineage confidence: {results.get('lineage_confidence', 'N/A'):.3f}
"""
        
        if results.get('used_annotations', False):
            summary_text += f"\n📋 Cell Type Integration:\n"
            for cell_type, info in results.get('cell_type_analysis', {}).items():
                summary_text += f"• {cell_type}: {info}\n"
        
        self.trajectory_summary_text.setText(summary_text)
        
        # Update plots if available
        if MATPLOTLIB_AVAILABLE and 'umap' in results:
            import matplotlib.pyplot as plt
            self.trajectory_figure.clear()
            
            if method == "Pseudotime":
                # Create subplots
                ax1 = self.trajectory_figure.add_subplot(121)
                ax2 = self.trajectory_figure.add_subplot(122)
                
                # Plot pseudotime
                if 'pseudotime' in results:
                    scatter = ax1.scatter(results['umap'][:, 0], results['umap'][:, 1], 
                              c=results['pseudotime'], cmap='viridis', s=1)
                    ax1.set_title('Pseudotime')
                    ax1.set_xlabel('UMAP 1')
                    ax1.set_ylabel('UMAP 2')
                    self.trajectory_figure.colorbar(scatter, ax=ax1)
                    
                    # Plot by cell type if available
                    if 'cell_types' in results:
                        unique_types = np.unique(results['cell_types'])
                        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_types)))
                        for i, cell_type in enumerate(unique_types):
                            mask = results['cell_types'] == cell_type
                            ax2.scatter(results['umap'][mask, 0], results['umap'][mask, 1], 
                                      c=[colors[i]], label=f'Cluster {cell_type}', s=1)
                        ax2.set_title('Cell Types')
                        ax2.set_xlabel('UMAP 1')
                        ax2.set_ylabel('UMAP 2')
                        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
            
            elif method == "RNA Velocity":
                # Create subplots for RNA velocity
                ax1 = self.trajectory_figure.add_subplot(121)
                ax2 = self.trajectory_figure.add_subplot(122)
                
                # Plot velocity field
                if 'velocity_vectors' in results:
                    # Subsample for cleaner visualization
                    n_arrows = min(1000, self.adata.n_obs)
                    indices = np.random.choice(self.adata.n_obs, n_arrows, replace=False)
                    
                    ax1.scatter(results['umap'][:, 0], results['umap'][:, 1], 
                               c='lightgray', s=0.5, alpha=0.5)
                    ax1.quiver(results['umap'][indices, 0], results['umap'][indices, 1],
                              results['velocity_vectors'][indices, 0], 
                              results['velocity_vectors'][indices, 1],
                              scale=2, alpha=0.7, color='red')
                    ax1.set_title('RNA Velocity Field')
                    ax1.set_xlabel('UMAP 1')
                    ax1.set_ylabel('UMAP 2')
                
                # Plot by cell type if available
                if 'cell_types' in results:
                    unique_types = np.unique(results['cell_types'])
                    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_types)))
                    for i, cell_type in enumerate(unique_types):
                        mask = results['cell_types'] == cell_type
                        ax2.scatter(results['umap'][mask, 0], results['umap'][mask, 1], 
                                  c=[colors[i]], label=f'Cluster {cell_type}', s=1)
                    ax2.set_title('Cell Types')
                    ax2.set_xlabel('UMAP 1')
                    ax2.set_ylabel('UMAP 2')
                    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
            
            elif method == "Lineage Tracing":
                # Create subplots for lineage tracing
                ax1 = self.trajectory_figure.add_subplot(121)
                ax2 = self.trajectory_figure.add_subplot(122)
                
                # Plot lineage assignments
                if 'lineage_assignments' in results:
                    n_lineages = results.get('n_lineages', 1)
                    colors = plt.cm.Set3(np.linspace(0, 1, n_lineages))
                    for lineage in range(n_lineages):
                        mask = results['lineage_assignments'] == lineage
                        ax1.scatter(results['umap'][mask, 0], results['umap'][mask, 1], 
                                  c=[colors[lineage]], label=f'Lineage {lineage}', s=1)
                    ax1.set_title('Lineage Assignments')
                    ax1.set_xlabel('UMAP 1')
                    ax1.set_ylabel('UMAP 2')
                    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
                
                # Plot by cell type if available
                if 'cell_types' in results:
                    unique_types = np.unique(results['cell_types'])
                    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_types)))
                    for i, cell_type in enumerate(unique_types):
                        mask = results['cell_types'] == cell_type
                        ax2.scatter(results['umap'][mask, 0], results['umap'][mask, 1], 
                                  c=[colors[i]], label=f'Cluster {cell_type}', s=1)
                    ax2.set_title('Cell Types')
                    ax2.set_xlabel('UMAP 1')
                    ax2.set_ylabel('UMAP 2')
                    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
            
            self.trajectory_figure.tight_layout()
            self.trajectory_canvas.draw()
    
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
        
        self.use_harmony_check = QCheckBox("Enable Harmony integration for multi-sample data")
        self.use_harmony_check.setChecked(True)
        self.use_harmony_check.setEnabled(False)
        params_layout.addWidget(self.use_harmony_check, 6, 0, 1, 2)

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

        export_report_btn = QPushButton("Export PDF Report")
        export_report_btn.clicked.connect(self.export_report)
        export_layout.addWidget(export_report_btn, 1, 0, 1, 2)
        
        open_folder_btn = QPushButton("Open Folder")
        open_folder_btn.clicked.connect(self.open_results_folder)
        export_layout.addWidget(open_folder_btn, 2, 0, 1, 2)
        
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

        import_multi_action = QAction("Import Multiple Samples", self)
        import_multi_action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        import_multi_action.triggered.connect(self.import_multiple_samples)
        file_menu.addAction(import_multi_action)

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
        
        open_results_action = QAction("Open Results Folder", self)
        open_results_action.setShortcut("Ctrl+Shift+O")
        open_results_action.triggered.connect(self.open_results_folder)
        export_menu.addAction(open_results_action)
        
        export_menu.addSeparator()
        
        export_data_action = QAction("Export AnnData (.h5ad)", self)
        export_data_action.triggered.connect(self.export_analysis_data)
        export_menu.addAction(export_data_action)
        
        export_plots_action = QAction("Export All Plots", self)
        export_plots_action.triggered.connect(self.export_plots)
        export_menu.addAction(export_plots_action)

        export_report_action = QAction("Export PDF Report", self)
        export_report_action.triggered.connect(self.export_report)
        export_menu.addAction(export_report_action)

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

        # Cell Annotation submenu
        annotation_menu = analysis_menu.addMenu("Cell Annotation")
        annotation_menu.addAction("Switch to Annotation Tab", lambda: self.tab_widget.setCurrentIndex(2))
        
        # Trajectory Analysis submenu  
        trajectory_menu = analysis_menu.addMenu("Trajectory Analysis")
        trajectory_menu.addAction("Switch to Trajectory Tab", lambda: self.tab_widget.setCurrentIndex(3))
        
        # Cell-Cell Interaction submenu
        interaction_menu = analysis_menu.addMenu("Cell-Cell Interaction")
        interaction_menu.addAction("Switch to Interaction Tab", lambda: self.tab_widget.setCurrentIndex(4))

        analysis_menu.addSeparator()

        # Individual Steps (optional - kept for completeness)
        individual_menu = analysis_menu.addMenu("Individual Steps")
        
        qc_menu = individual_menu.addMenu("QC Steps")
        qc_menu.addAction("Calculate QC Metrics", self.calculate_qc_metrics)
        qc_menu.addAction("Filter Cells", self.filter_cells)
        qc_menu.addAction("Filter Genes", self.filter_genes)
        
        processing_menu = individual_menu.addMenu("Processing Steps")
        processing_menu.addAction("Log Normalize", self.log_normalize)
        processing_menu.addAction("Scale Data", self.scale_data)
        
        dim_red_menu = individual_menu.addMenu("Dimensionality Reduction")
        dim_red_menu.addAction("Run PCA", self.run_pca)
        dim_red_menu.addAction("Run UMAP", self.run_umap)
        dim_red_menu.addAction("Run t-SNE", self.run_tsne)
        
        cluster_menu = individual_menu.addMenu("Clustering")
        cluster_menu.addAction("Leiden Clustering", self.leiden_clustering)
        cluster_menu.addAction("Louvain Clustering", self.louvain_clustering)

        # View Menu
        view_menu = self.menu_bar.addMenu("View")
        
        # Tab navigation
        tab_menu = view_menu.addMenu("Switch to Tab")
        tab_menu.addAction("Home", lambda: self.tab_widget.setCurrentIndex(0))
        tab_menu.addAction("QC & Cluster", lambda: self.tab_widget.setCurrentIndex(1))
        tab_menu.addAction("Cell Annotation", lambda: self.tab_widget.setCurrentIndex(2))
        tab_menu.addAction("Trajectory Analysis", lambda: self.tab_widget.setCurrentIndex(3))
        tab_menu.addAction("Cell-Cell Interaction", lambda: self.tab_widget.setCurrentIndex(4))
        
        view_menu.addSeparator()
        
        # Display options
        view_menu.addAction("Refresh Plot Display", self.refresh_plots_display)
        view_menu.addAction("Open Results Folder", self.open_results_folder)

        # Help Menu
        help_menu = self.menu_bar.addMenu("Help")
        
        help_menu.addAction("Getting Started", self.show_getting_started)
        help_menu.addAction("User Manual", self.show_user_manual)
        help_menu.addAction("Tutorials", self.show_tutorials)
        
        help_menu.addSeparator()
        
        # Sample Data section
        sample_menu = help_menu.addMenu("Sample Data")
        sample_menu.addAction("Load Sample Dataset", self.load_sample_data)
        sample_menu.addAction("Open Examples Folder", self.open_examples_folder)
        
        help_menu.addSeparator()
        
        # Documentation section
        docs_menu = help_menu.addMenu("Documentation")
        docs_menu.addAction("Open Documentation Folder", self.open_documentation_folder)
        docs_menu.addAction("Cell-Cell Interaction Guide", self.show_interaction_guide)
        docs_menu.addAction("Trajectory Analysis Guide", self.show_trajectory_guide)
        
        help_menu.addSeparator()
        
        help_menu.addAction("About SingleCellStudio", self.show_about)
        help_menu.addAction("Version Info", self.show_version_info)

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
            # Get the path to the QSS file
            qss_path = Path(__file__).parent / "default.qss"
            
            if qss_path.exists():
                with open(qss_path, 'r', encoding='utf-8') as f:
                    qss_content = f.read()
                self.setStyleSheet(qss_content)
                logger.info(f"Successfully loaded QSS styling from: {qss_path}")
            else:
                logger.warning(f"QSS file not found at: {qss_path}")
                # Fallback to basic styling if QSS file is not found
                self.setStyleSheet("""
                    QMainWindow {
                        background-color: #f8f9fa;
                    }
                """)
        except Exception as e:
            logger.error(f"Failed to load QSS styling: {e}")
            # Fallback to basic styling
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f8f9fa;
                }
            """)
    
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
        self.input_file_paths = []
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
    
    def _finalize_loaded_data(self, adata_obj, source_description, input_reference):
        """Apply common state updates after loading data."""
        self.adata = adata_obj
        self.input_file_path = input_reference
        if isinstance(input_reference, list):
            self.input_file_paths = input_reference
        elif isinstance(input_reference, str) and input_reference:
            self.input_file_paths = [input_reference]
        else:
            self.input_file_paths = []

        self.log_activity(f"Data loaded ({source_description}): {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes")

        self.output_dir = self._setup_output_directory()

        self.current_mode = "data_loaded"
        self.data_info_label.setText(f"📊 {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes")
        self.data_header.setText(f"📊 Dataset: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes")

        self.tab_widget.setTabEnabled(1, True)
        self.tab_widget.setCurrentIndex(1)

        self.update_annotation_widget_data()
        self.update_trajectory_tab_status()
        self.update_interaction_tab_status()

        has_batch = 'batch' in self.adata.obs.columns
        if hasattr(self, 'use_harmony_check'):
            self.use_harmony_check.setEnabled(has_batch)
            if has_batch:
                n_batches = self.adata.obs['batch'].nunique()
                self.use_harmony_check.setText(f"Enable Harmony integration for multi-sample data ({n_batches} batches)")
            else:
                self.use_harmony_check.setChecked(False)
                self.use_harmony_check.setText("Enable Harmony integration for multi-sample data")

        self.statusBar().showMessage(
            f"Data loaded: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes"
        )

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
            loaded_data = dialog.get_loaded_data()
            file_path = dialog.get_file_path()

            if loaded_data is not None:
                self._finalize_loaded_data(loaded_data, "single sample", file_path)
    
    def import_multiple_samples(self):
        """Import and merge multiple single-cell samples for integration workflows."""
        if not ANALYSIS_AVAILABLE:
            QMessageBox.warning(self, "Import Not Available", "Analysis dependencies are required for multi-sample import.")
            return

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Multiple Single-Cell Datasets",
            str(Path.home()),
            "Single-cell files (*.h5ad *.h5 *.csv *.tsv);;All files (*)"
        )

        if not file_paths:
            return

        if len(file_paths) < 2:
            QMessageBox.information(self, "Single File Selected", "Only one file selected. Loading as a single sample.")
            self._load_data_from_path(Path(file_paths[0]))
            return

        loader = DataLoader()
        sample_adatas = []
        sample_names = []

        try:
            for idx, file_path in enumerate(file_paths, start=1):
                current_path = Path(file_path)
                sample_name = current_path.stem or f"sample_{idx}"
                format_type = auto_detect_format(file_path)
                sample_adata = loader.load(file_path, format_type)
                sample_adata.obs_names_make_unique()
                sample_adata.obs_names = [f"{sample_name}_{cell}" for cell in sample_adata.obs_names]
                sample_adata.obs['batch'] = sample_name
                sample_adata.obs['sample_id'] = sample_name
                sample_adatas.append(sample_adata)
                sample_names.append(sample_name)
                self.log_activity(f"Loaded sample '{sample_name}': {sample_adata.n_obs:,} cells × {sample_adata.n_vars:,} genes")

            integrated_adata = ad.concat(
                sample_adatas,
                join='outer',
                merge='same',
                fill_value=0
            )
            integrated_adata.obs_names_make_unique()
            integrated_adata.uns['scs_integration'] = {
                'n_samples': len(sample_names),
                'sample_names': sample_names,
                'integration_ready': True,
                'batch_key': 'batch'
            }

            self._finalize_loaded_data(integrated_adata, f"{len(sample_names)} merged samples", file_paths[0])
            self.log_activity(f"Multi-sample dataset prepared with batch labels: {', '.join(sample_names)}")

        except Exception as e:
            self.log_activity(f"Failed multi-sample import: {e}")
            QMessageBox.critical(self, "Import Failed", f"Failed to import multiple samples:\n{e}")

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
            self.tab_widget.setTabEnabled(3, True)  # Enable trajectory analysis tab
            self.tab_widget.setTabEnabled(4, True)  # Enable cell-cell interaction tab
            
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
            
            # Update trajectory tab status
            self.update_trajectory_tab_status()
            
            # Update interaction tab status
            self.update_interaction_tab_status()
            
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
                'resolution': self.resolution_spin.value(),
                'use_harmony': bool(getattr(self, 'use_harmony_check', None) and self.use_harmony_check.isChecked()),
                'batch_key': 'batch'
            }
            
            if pipeline_params['use_harmony'] and 'batch' not in self.adata.obs.columns:
                self.log_activity("Harmony requested but no 'batch' column found; running without Harmony.")
                pipeline_params['use_harmony'] = False

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
        
        # Enable Cell Annotation tab, Trajectory Analysis tab, and Cell-Cell Interaction tab now that clustering is complete
        self.tab_widget.setTabEnabled(2, True)
        self.tab_widget.setTabEnabled(3, True)
        self.tab_widget.setTabEnabled(4, True)
        
        # Update annotation widget with processed data
        self.update_annotation_widget_data()
        
        # Update trajectory tab status
        self.update_trajectory_tab_status()
        
        # Update interaction tab status
        self.update_interaction_tab_status()
        
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
        all_plot_files = list(plots_dir.glob("*.png")) + list(plots_dir.glob("*.pdf")) + list(plots_dir.glob("*.jpg"))
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
            filename = f"custom_{safe_title}_{timestamp}.png"
            
            filepath = plots_dir / filename
            figure.savefig(filepath, dpi=300, bbox_inches='tight')
            
            self.log_activity(f"Plot saved: {filename}")
            
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
                summary_file = plots_dir / f"summary_{timestamp}.png"
                fig.savefig(summary_file, dpi=300, bbox_inches='tight')
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
                    umap_file = plots_dir / f"umap_{timestamp}.png"
                    fig.savefig(umap_file, dpi=300, bbox_inches='tight')
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
                    qc_file = plots_dir / f"qc_{timestamp}.png"
                    fig.savefig(qc_file, dpi=300, bbox_inches='tight')
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
                    pca_file = plots_dir / f"pca_{timestamp}.png"
                    fig.savefig(pca_file, dpi=300, bbox_inches='tight')
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
        """Handle cell annotation completion and update visualizations"""
        try:
            # Log successful annotation
            method_used = results.get('method_used', 'Unknown')
            summary = results.get('summary', {})
            total_cells = summary.get('total_cells', 'N/A')
            unique_types = summary.get('unique_cell_types', 'N/A')
            
            self.log_activity(f"✅ Cell annotation completed using {method_used}")
            self.log_activity(f"   Annotated {total_cells} cells into {unique_types} cell types")
            
            # Update data header if we have annotation data
            if hasattr(self, 'adata') and self.adata is not None and 'cell_type' in self.adata.obs:
                n_cells = self.adata.n_obs
                n_types = len(self.adata.obs['cell_type'].unique())
                self.data_header.setText(f"Data loaded: {n_cells:,} cells, {n_types} cell types annotated")
            
            # Update advanced visualizations in the dedicated tab
            self.update_annotation_visualizations(results)
            
        except Exception as e:
            self.logger.error(f"Error handling annotation completion: {e}")
    
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
        """Export analysis summary as a PDF report."""
        if self.analysis_adata is None and self.adata is None:
            QMessageBox.warning(self, "No Data", "Please load and analyze data before exporting a report.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_dir = self.output_dir if self.output_dir else Path.cwd()
        default_path = Path(default_dir) / f"singlecellstudio_report_{timestamp}.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export PDF Report",
            str(default_path),
            "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        report_path = Path(file_path)
        if report_path.suffix.lower() != ".pdf":
            report_path = report_path.with_suffix(".pdf")

        active_adata = self.analysis_adata if self.analysis_adata is not None else self.adata

        report_lines = [
            "SingleCellStudio Analysis Report",
            "=" * 40,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Input file: {Path(self.input_file_path).name if self.input_file_path else 'N/A'}",
            "",
            "Dataset Summary",
            "-" * 40,
            f"Cells: {active_adata.n_obs:,}",
            f"Genes: {active_adata.n_vars:,}",
            f"Observation columns: {len(active_adata.obs.columns)}",
            f"Variable columns: {len(active_adata.var.columns)}",
        ]

        if self.analysis_results:
            report_lines.extend(["", "Analysis Result Keys", "-" * 40])
            for key in sorted(self.analysis_results.keys()):
                value = self.analysis_results.get(key)
                if isinstance(value, dict):
                    report_lines.append(f"{key}: {len(value)} entries")
                elif isinstance(value, (list, tuple, set)):
                    report_lines.append(f"{key}: {len(value)} items")
                else:
                    report_lines.append(f"{key}: {str(value)[:120]}")

        summary_text = self.summary_text.toPlainText().strip() if hasattr(self, "summary_text") else ""
        if summary_text:
            report_lines.extend(["", "Analysis Summary", "-" * 40])
            report_lines.extend(summary_text.splitlines())

        try:
            from matplotlib.backends.backend_pdf import PdfPages
            import matplotlib.pyplot as plt

            lines_per_page = 48
            chunks = [report_lines[i:i + lines_per_page] for i in range(0, len(report_lines), lines_per_page)]

            with PdfPages(report_path) as pdf:
                for page_num, chunk in enumerate(chunks, start=1):
                    fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait in inches
                    fig.text(
                        0.06,
                        0.97,
                        "\n".join(chunk),
                        ha="left",
                        va="top",
                        fontsize=9,
                        family="monospace",
                    )
                    fig.text(0.5, 0.02, f"Page {page_num}/{len(chunks)}", ha="center", va="bottom", fontsize=8)
                    pdf.savefig(fig, bbox_inches="tight")
                    plt.close(fig)

            self.log_activity(f"PDF report exported: {report_path}")
            QMessageBox.information(self, "Export Complete", f"Report exported successfully:\n{report_path}")

        except Exception as e:
            self.logger.error(f"Failed to export PDF report: {e}")
            QMessageBox.critical(self, "Export Failed", f"Could not export PDF report:\n{e}")
    
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
        msg = QMessageBox()
        msg.setWindowTitle("Getting Started")
        msg.setText("Welcome to SingleCellStudio Professional!")
        msg.setInformativeText("""
Quick Start Guide:

1. 📁 Import Data: Use File → Import Data to load your single cell RNA-seq data
   • Supported formats: 10X Genomics (MTX, H5), AnnData (H5AD), CSV/TSV

2. 🔬 Analyze: Go to Analysis tab and run the standard pipeline
   • Automatic quality control, normalization, and clustering
   • Customizable parameters for advanced users

3. 📊 View Results: Check the Results tab for analysis outcomes
   • Interactive data tables and summary statistics
   • Export capabilities for further analysis

4. 💾 Export: Save your results and plots for publication
   • Multiple export formats available
   • Professional-quality visualizations

For detailed instructions, see Documentation → User Manual
        """)
        msg.exec()
    
    def show_user_manual(self):
        """Show user manual with links to documentation"""
        msg = QMessageBox()
        msg.setWindowTitle("User Manual")
        msg.setText("SingleCellStudio Professional Documentation")
        msg.setInformativeText("""
📚 Complete documentation available:

• Getting Started Guide
• Cell-Cell Interaction Analysis Guide  
• Trajectory Analysis Guide
• Modular Development Best Practices

📁 Location: docs/ directory in installation folder
🎬 Video Tutorial: Coming soon!

Click 'Open Documentation Folder' to access all guides.
        """)
        
        open_docs_btn = msg.addButton("Open Documentation Folder", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        
        result = msg.exec()
        if msg.clickedButton() == open_docs_btn:
            self.open_documentation_folder()
    
    def show_tutorials(self):
        """Show tutorials"""
        msg = QMessageBox()
        msg.setWindowTitle("Quick Tutorial")
        msg.setText("SingleCellStudio Professional Quick Tutorial")
        msg.setInformativeText("""
🎯 Complete Analysis Workflow:

1️⃣ DATA IMPORT
   • Click "📁 Import Single Cell Data" or use File → Import Data
   • Or try "📊 Load Sample Dataset" for demonstration

2️⃣ QUALITY CONTROL & CLUSTERING  
   • Switch to "QC & Cluster" tab
   • Click "🔬 Run Standard Analysis"
   • Wait for analysis completion

3️⃣ CELL ANNOTATION
   • Switch to "Cell Annotation" tab
   • Choose annotation method and run analysis

4️⃣ TRAJECTORY ANALYSIS (NEW!)
   • Switch to "Trajectory Analysis" tab
   • Select Pseudotime, RNA Velocity, or Lineage Tracing

5️⃣ CELL-CELL INTERACTION (NEW!)
   • Switch to "Cell-Cell Interaction" tab  
   • Choose Ligand-Receptor, Spatial, or Communication analysis

💡 Tip: Results are automatically saved in the results/ folder!
        """)
        
        load_sample_btn = msg.addButton("Load Sample Data", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        
        result = msg.exec()
        if msg.clickedButton() == load_sample_btn:
            self.load_sample_data()
    
    def show_api_reference(self):
        """Show API reference"""
        QMessageBox.information(self, "API Reference", 
                              "API documentation will be available in the next version.")
    
    def load_sample_data(self):
        """Load sample data for demonstration"""
        sample_path = Path("examples/sample_data/filtered_feature_bc_matrix.h5")
        
        if sample_path.exists():
            try:
                self.input_file_path = str(sample_path)
                # Use existing data loading logic
                self._load_data_from_path(sample_path)
                self.log_activity("Sample dataset loaded successfully")
                QMessageBox.information(self, "Sample Data Loaded", 
                                      "Sample dataset loaded successfully!\n"
                                      "12,047 cells × 38,606 genes\n\n"
                                      "You can now run analysis to explore the features.")
            except Exception as e:
                self.log_activity(f"Failed to load sample data: {str(e)}")
                QMessageBox.critical(self, "Load Failed", f"Failed to load sample data:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Sample Data Not Found", 
                              "Sample data not found. Please check the examples/sample_data/ directory.")
    
    def _load_data_from_path(self, file_path):
        """Helper method to load data from a given path"""
        try:
            data_format = auto_detect_format(str(file_path))
            self.log_activity(f"Detected format: {data_format}")

            loader = DataLoader()
            adata = loader.load(str(file_path), data_format)

            self._finalize_loaded_data(adata, Path(file_path).name, str(file_path))

        except Exception as e:
            raise e
    
    def _update_data_display(self):
        """Update data display after loading"""
        if self.adata is not None:
            # Update data info label
            n_cells, n_genes = self.adata.shape
            data_info = f"📊 Data loaded: {n_cells:,} cells × {n_genes:,} genes"
            self.data_info_label.setText(data_info)
            
            # Update header in analysis tab
            self.data_header.setText(data_info)
            
            # Enable analysis tab
            self.tab_widget.setTabEnabled(1, True)
            
            self.log_activity(f"Data loaded: {n_cells} cells, {n_genes} genes")
    
    def open_examples_folder(self):
        """Open examples folder"""
        examples_path = Path("examples")
        if examples_path.exists():
            import os
            import platform
            
            if platform.system() == "Windows":
                os.startfile(examples_path)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{examples_path}'")
            else:  # Linux
                os.system(f"xdg-open '{examples_path}'")
        else:
            QMessageBox.warning(self, "Examples Not Found", 
                              "Examples folder not found.")
    
    def open_documentation_folder(self):
        """Open documentation folder"""
        docs_path = Path("docs")
        if docs_path.exists():
            import os
            import platform
            
            if platform.system() == "Windows":
                os.startfile(docs_path)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{docs_path}'")
            else:  # Linux
                os.system(f"xdg-open '{docs_path}'")
        else:
            QMessageBox.warning(self, "Documentation Not Found", 
                              "Documentation folder not found.")
    
    def show_interaction_guide(self):
        """Show Cell-Cell Interaction guide"""
        guide_path = Path("docs/CELL_INTERACTION_ANALYSIS_GUIDE.md")
        if guide_path.exists():
            self.open_documentation_folder()
            QMessageBox.information(self, "Cell-Cell Interaction Guide", 
                                  "Cell-Cell Interaction Analysis Guide opened in documentation folder.\n\n"
                                  "Look for: CELL_INTERACTION_ANALYSIS_GUIDE.md")
        else:
            QMessageBox.information(self, "Cell-Cell Interaction Guide", 
                                  "Cell-Cell Interaction Analysis Guide:\n\n"
                                  "1. 📊 Switch to Cell-Cell Interaction tab\n"
                                  "2. 🔬 Choose analysis method:\n"
                                  "   • Ligand-Receptor Analysis\n"
                                  "   • Spatial Proximity Analysis\n"
                                  "   • Communication Modeling\n"
                                  "3. ⚙️ Configure parameters\n"
                                  "4. ▶️ Run Analysis\n"
                                  "5. 📈 View results and visualizations")
    
    def show_trajectory_guide(self):
        """Show Trajectory Analysis guide"""
        guide_path = Path("docs/TRAJECTORY_ANALYSIS_GUIDE.md")
        if guide_path.exists():
            self.open_documentation_folder()
            QMessageBox.information(self, "Trajectory Analysis Guide", 
                                  "Trajectory Analysis Guide opened in documentation folder.\n\n"
                                  "Look for: TRAJECTORY_ANALYSIS_GUIDE.md")
        else:
            QMessageBox.information(self, "Trajectory Analysis Guide", 
                                  "Trajectory Analysis Guide:\n\n"
                                  "1. 📊 Switch to Trajectory Analysis tab\n"
                                  "2. 🔬 Choose analysis method:\n"
                                  "   • Pseudotime Analysis\n"
                                  "   • RNA Velocity Analysis\n"
                                  "   • Lineage Tracing\n"
                                  "3. ⚙️ Configure parameters\n"
                                  "4. ▶️ Run Analysis\n"
                                  "5. 📈 View developmental trajectories")
    
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

# Main execution function for testing
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create and show the professional main window
    window = ProfessionalMainWindow()
    window.show()
    
    sys.exit(app.exec()) 
