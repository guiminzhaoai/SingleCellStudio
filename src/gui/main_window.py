"""
SingleCellStudio Main Window

Basic implementation of the main application window.
This is a minimal version - full functionality will be implemented gradually.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QMessageBox, QMenuBar, QStatusBar, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction

# Import data import dialog
try:
    from .data_import_dialog import DataImportDialog
    from .analysis_window import AnalysisWindow
except ImportError:
    try:
        # Fallback import
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from data_import_dialog import DataImportDialog
        from analysis_window import AnalysisWindow
    except ImportError:
        DataImportDialog = None
        AnalysisWindow = None

# Import version info
try:
    from version import __version__, VERSION_STRING
except ImportError:
    __version__ = "0.1.0"
    VERSION_STRING = "0.1.0-dev"

class MainWindow(QMainWindow):
    """Main application window for SingleCellStudio"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"SingleCellStudio {VERSION_STRING}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Welcome message
        welcome_label = QLabel("Welcome to SingleCellStudio!")
        welcome_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Version info
        version_label = QLabel(f"Version: {VERSION_STRING}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        # Status message
        status_text = QTextEdit()
        status_text.setReadOnly(True)
        status_text.setText("""
SingleCellStudio - Professional Single Cell Analysis Software

🚀 STATUS: Core Data Loading Implemented!

Current Features:
✅ Application framework initialized
✅ PySide6 GUI system working
✅ Cross-platform compatibility (Windows/Linux/Mac)
✅ Matplotlib integration for plotting
✅ Project structure established
✅ Comprehensive testing framework
✅ Data loading system implemented
✅ Support for 10X Genomics formats (MTX + H5)
✅ Support for AnnData H5AD format
✅ Support for CSV/TSV formats
✅ Automatic format detection
✅ Data validation and quality control
✅ Professional data import interface

🎯 READY TO TEST:
• Use File → Import Data to load your scRNA-seq data
• Or test via command line: python examples/test_data_loading.py <path>

Supported Data Formats:
📁 10X Genomics MTX folder (matrix.mtx.gz + barcodes.tsv.gz + features.tsv.gz)
📄 10X Genomics H5 files (.h5)
📄 AnnData H5AD files (.h5ad)
📄 CSV/TSV files

Next Development Steps:
🔄 Create analysis pipeline interface
🔄 Add interactive visualization panels
🔄 Build project management system
🔄 Integrate single cell analysis algorithms

For a preview of the full intended interface, run:
python prototype/basic_gui_demo.py

Ready to load and analyze your single cell data!
        """)
        layout.addWidget(status_text)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        import_btn = QPushButton("Import Data")
        import_btn.clicked.connect(self.import_data)
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                font-size: 14px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(import_btn)
        
        demo_btn = QPushButton("Launch Interface Demo")
        demo_btn.clicked.connect(self.launch_demo)
        button_layout.addWidget(demo_btn)
        
        about_btn = QPushButton("About SingleCellStudio")
        about_btn.clicked.connect(self.show_about)
        button_layout.addWidget(about_btn)
        
        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self.close)
        button_layout.addWidget(exit_btn)
        
        layout.addLayout(button_layout)
        
        central_widget.setLayout(layout)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
        
        # Apply basic styling
        self.apply_styling()
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Import data
        import_action = QAction('Import Data...', self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        demo_action = QAction('Launch Demo', self)
        demo_action.triggered.connect(self.launch_demo)
        help_menu.addAction(demo_action)
    
    def import_data(self):
        """Import single cell data"""
        if DataImportDialog is None:
            QMessageBox.information(
                self,
                "Feature Under Development",
                "Data import functionality is currently under development.\n\n"
                "You can test the data loading functionality using:\n"
                "python examples/test_data_loading.py <data_path>\n\n"
                "Supported formats:\n"
                "• 10X Genomics MTX folder\n"
                "• 10X Genomics H5 file\n"
                "• AnnData H5AD file\n"
                "• CSV/TSV files"
            )
            return
        
        dialog = DataImportDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the loaded data and file path
            adata = dialog.get_loaded_data()
            file_path = dialog.get_file_path()
            
            if adata is not None:
                # Update status bar
                self.statusBar().showMessage(
                    f"Data loaded: {adata.n_obs:,} cells × {adata.n_vars:,} genes"
                )
                
                # Open analysis window with file path
                self.open_analysis_window(adata, file_path)
    
    def open_analysis_window(self, adata, input_file_path=None):
        """Open the analysis window with loaded data"""
        if AnalysisWindow is None:
            QMessageBox.warning(
                self,
                "Analysis Window Not Available",
                "Analysis window is not available. Please check the installation."
            )
            return
        
        try:
            # Create and show analysis window with input file path
            self.analysis_window = AnalysisWindow(adata, self, input_file_path)
            self.analysis_window.show()
            
            # Optionally minimize the main window
            self.showMinimized()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Opening Analysis Window",
                f"Failed to open analysis window:\n{str(e)}"
            )
    
    def create_status_bar(self):
        """Create the status bar"""
        status_bar = self.statusBar()
        status_bar.showMessage("SingleCellStudio - Ready for Development")
    
    def apply_styling(self):
        """Apply basic styling to the window"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
                margin: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                margin: 10px;
            }
        """)
    
    def launch_demo(self):
        """Launch the interface demo"""
        try:
            import subprocess
            import sys
            from pathlib import Path
            
            # Get the prototype demo path
            demo_path = Path(__file__).parent.parent.parent / "prototype" / "basic_gui_demo.py"
            
            if demo_path.exists():
                # Launch demo in a separate process
                subprocess.Popen([sys.executable, str(demo_path)])
                
                # Show info message
                msg = QMessageBox()
                msg.setWindowTitle("Demo Launched")
                msg.setText("Interface Demo Launched!")
                msg.setInformativeText("The prototype demo has been launched in a separate window.\n\nThis shows the intended professional interface for SingleCellStudio.")
                msg.exec()
            else:
                self.show_error("Demo file not found", f"Could not find demo at: {demo_path}")
                
        except Exception as e:
            self.show_error("Launch Error", f"Failed to launch demo: {e}")
    
    def show_about(self):
        """Show about dialog"""
        msg = QMessageBox()
        msg.setWindowTitle("About SingleCellStudio")
        msg.setText(f"SingleCellStudio {VERSION_STRING}")
        msg.setInformativeText(
            "Commercial Single Cell Transcriptome Analysis Software\n\n"
            "A professional-grade platform for single cell RNA-seq analysis\n"
            "designed to rival industry leaders like CLC Workbench.\n\n"
            "© 2024 SingleCellStudio Inc.\n"
            "All rights reserved.\n\n"
            "Status: Development Version\n"
            "Target Release: 2025"
        )
        msg.setDetailedText(
            "Technology Stack:\n"
            "• Frontend: PySide6\n"
            "• Analysis: scanpy, pandas, numpy\n" 
            "• Visualization: matplotlib, plotly\n"
            "• Platform: Windows, Linux, macOS\n\n"
            "Key Features (Planned):\n"
            "• Quality Control & Preprocessing\n"
            "• Dimensionality Reduction (PCA, UMAP, t-SNE)\n"
            "• Clustering & Cell Type Annotation\n"
            "• Differential Expression Analysis\n"
            "• Trajectory Analysis & RNA Velocity\n"
            "• Interactive Visualizations\n"
            "• Pathway Enrichment Analysis\n"
            "• Batch Effect Correction\n"
            "• Multi-sample Integration\n"
            "• Publication-quality Plots"
        )
        msg.exec()
    
    def show_error(self, title, message):
        """Show error dialog"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()
    
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self, 
            'Exit SingleCellStudio',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore() 