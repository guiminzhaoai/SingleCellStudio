"""
Modular Professional Main Window

This is a refactored version of the professional main window that uses
the module registry system for better modularity and maintainability.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QMessageBox, QMenuBar, QStatusBar,
    QTabWidget, QGroupBox, QProgressBar, QSplitter
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QAction, QKeySequence

# Import module system
from src.gui.modules.module_registry import registry, BaseGUIModule
from src.gui.modules.data_manager import data_manager

# Import existing modules (these will be automatically registered)
from src.gui.modules.example_module import ExampleModule

try:
    from ..version import __version__, VERSION_STRING
except ImportError:
    __version__ = "0.2.0"
    VERSION_STRING = "0.2.0-dev"

logger = logging.getLogger(__name__)

class ModularMainWindow(QMainWindow):
    """Modular main window that dynamically loads GUI modules"""
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Data variables
        self.adata = None
        self.analysis_adata = None
        self.analysis_results = None
        self.input_file_path = None
        self.output_dir = None
        
        # Module system
        self.loaded_modules: Dict[str, BaseGUIModule] = {}
        self.data_manager = data_manager
        
        # UI components
        self.tab_widget = None
        self.progress_bar = None
        self.activity_log = None
        self.memory_label = None
        
        # Initialize
        self.setup_module_system()
        self.init_ui()
        self.load_modules()
    
    def setup_module_system(self):
        """Set up the module registry system"""
        try:
            # Register built-in modules
            registry.register_module_class(ExampleModule)
            
            # Auto-discover modules in the modules directory
            modules_dir = Path(__file__).parent / "modules"
            registry.auto_discover_modules(modules_dir)
            
            self.logger.info("Module system initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to setup module system: {e}")
    
    def init_ui(self):
        """Initialize the modularized user interface"""
        self.setWindowTitle(f"SingleCellStudio {VERSION_STRING} - Modular Edition")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create tab widget for different modes
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        
        # Add core tabs
        self.create_home_tab()
        
        # Module tabs will be added by load_modules()
        
        main_layout.addWidget(self.tab_widget)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        self.central_widget.setLayout(main_layout)
        
        # Create professional menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
        
        # Apply styling
        self.apply_professional_styling()
    
    def create_home_tab(self):
        """Create the home tab"""
        home_widget = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("SingleCellStudio - Modular Edition")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #2c3e50; margin: 20px;")
        layout.addWidget(header)
        
        # Info panel
        info_group = QGroupBox("System Information")
        info_layout = QVBoxLayout()
        
        # Data info
        self.data_info_label = QLabel("No data loaded")
        self.data_info_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(self.data_info_label)
        
        # Module info
        self.module_info_text = QTextEdit()
        self.module_info_text.setReadOnly(True)
        self.module_info_text.setMaximumHeight(200)
        info_layout.addWidget(self.module_info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Activity log
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()
        
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(250)
        self.activity_log.setText("Welcome to SingleCellStudio Modular Edition!")
        log_layout.addWidget(self.activity_log)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        home_widget.setLayout(layout)
        
        self.tab_widget.addTab(home_widget, "Home")
    
    def load_modules(self):
        """Load and instantiate all registered modules"""
        try:
            module_info = ["🔧 Registered Modules:", "=" * 30]
            
            # Get all registered module classes
            for module_name, module_class in registry._module_classes.items():
                try:
                    # Instantiate the module
                    module_instance = registry.instantiate_module(module_name, self)
                    
                    if module_instance and module_instance.enabled:
                        # Set data manager for the module
                        module_instance.data_manager = self.data_manager
                        
                        self.loaded_modules[module_name] = module_instance
                        
                        # Create tab for the module
                        widget = module_instance.create_widget(self)
                        if widget:
                            self.tab_widget.addTab(widget, module_instance.display_name)
                        
                        # Connect signals if the module has them
                        self.connect_module_signals(module_instance)
                        
                        module_info.append(f"✅ {module_instance.display_name} v{module_instance.version}")
                        module_info.append(f"   {module_instance.description}")
                        
                        self.log_activity(f"Loaded module: {module_instance.display_name}")
                        
                    else:
                        module_info.append(f"❌ {module_name} (disabled or failed)")
                        
                except Exception as e:
                    self.logger.error(f"Failed to load module {module_name}: {e}")
                    module_info.append(f"❌ {module_name} (error: {str(e)})")
            
            # Update module info display
            if hasattr(self, 'module_info_text'):
                self.module_info_text.setText("\n".join(module_info))
            
            self.logger.info(f"Loaded {len(self.loaded_modules)} modules")
            
        except Exception as e:
            self.logger.error(f"Error loading modules: {e}")
    
    def connect_module_signals(self, module: BaseGUIModule):
        """Connect module signals to main window handlers"""
        try:
            # Connect common signals if they exist
            if hasattr(module, 'analysis_requested'):
                module.analysis_requested.connect(self.on_module_analysis_requested)
            
            if hasattr(module, 'data_updated'):
                module.data_updated.connect(self.on_module_data_updated)
                
        except Exception as e:
            self.logger.error(f"Error connecting signals for module {module.module_name}: {e}")
    
    def create_menu_bar(self):
        """Create menu bar with module contributions"""
        self.menu_bar = self.menuBar()
        
        # File Menu
        file_menu = self.menu_bar.addMenu("File")
        
        import_action = QAction("Import Data", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Modules Menu - dynamically populated
        modules_menu = self.menu_bar.addMenu("Modules")
        self.populate_modules_menu(modules_menu)
        
        # Help Menu
        help_menu = self.menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def populate_modules_menu(self, modules_menu):
        """Populate modules menu with actions from loaded modules"""
        try:
            modules_menu.clear()
            
            # Add module management actions
            refresh_action = QAction("Refresh Modules", self)
            refresh_action.triggered.connect(self.refresh_modules)
            modules_menu.addAction(refresh_action)
            
            modules_menu.addSeparator()
            
            # Add actions from modules
            for module_name, module in self.loaded_modules.items():
                try:
                    actions = module.get_menu_actions()
                    if actions:
                        # Create submenu for this module
                        module_submenu = modules_menu.addMenu(module.display_name)
                        
                        for action_info in actions:
                            action = QAction(action_info['text'], self)
                            action.triggered.connect(action_info['callback'])
                            
                            if 'shortcut' in action_info:
                                action.setShortcut(action_info['shortcut'])
                            
                            module_submenu.addAction(action)
                            
                except Exception as e:
                    self.logger.error(f"Error adding menu actions for {module_name}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error populating modules menu: {e}")
    
    def create_status_bar(self):
        """Create status bar"""
        status_bar = self.statusBar()
        status_bar.showMessage("SingleCellStudio Modular - Ready")
        
        # Add permanent widgets
        self.memory_label = QLabel("Memory: 0 MB")
        status_bar.addPermanentWidget(self.memory_label)
        
        # Update memory usage periodically
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_usage)
        self.memory_timer.start(5000)
    
    def apply_professional_styling(self):
        """Apply professional styling"""
        try:
            # Get the path to the QSS file
            qss_path = Path(__file__).parent / "default.qss"
            
            if qss_path.exists():
                with open(qss_path, 'r', encoding='utf-8') as f:
                    qss_content = f.read()
                self.setStyleSheet(qss_content)
                self.logger.info(f"Successfully loaded QSS styling from: {qss_path}")
            else:
                self.logger.warning(f"QSS file not found at: {qss_path}")
                # Fallback styling
                self.setStyleSheet("""
                    QMainWindow {
                        background-color: #f8f9fa;
                    }
                """)
        except Exception as e:
            self.logger.error(f"Failed to load QSS styling: {e}")
            self.setStyleSheet("QMainWindow { background-color: #f8f9fa; }")
    
    # Data management methods
    def import_data(self):
        """Import data and distribute to modules"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Data", str(Path.home()), 
            "H5AD files (*.h5ad);;All files (*)"
        )
        
        if file_path:
            try:
                import anndata as ad
                self.adata = ad.read_h5ad(file_path)
                self.input_file_path = file_path
                
                # Update data manager
                self.data_manager.set_main_data(self.adata, "main_window")
                
                # Update UI
                self.data_info_label.setText(f"📊 {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes")
                
                # Distribute data to all modules
                for module in self.loaded_modules.values():
                    module.set_data(self.adata)
                
                self.log_activity(f"Data loaded: {Path(file_path).name}")
                self.statusBar().showMessage(f"Data loaded: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes")
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import data:\n{str(e)}")
                self.logger.error(f"Import error: {e}")
    
    def refresh_modules(self):
        """Refresh the module system"""
        try:
            self.log_activity("Refreshing modules...")
            
            # Clean up existing modules
            for module in self.loaded_modules.values():
                module.cleanup()
            
            # Clear tabs (except home)
            while self.tab_widget.count() > 1:
                self.tab_widget.removeTab(1)
            
            self.loaded_modules.clear()
            
            # Reload modules
            self.setup_module_system()
            self.load_modules()
            
            # Refresh menu
            modules_menu = None
            for action in self.menu_bar.actions():
                if action.text() == "Modules":
                    modules_menu = action.menu()
                    break
            
            if modules_menu:
                self.populate_modules_menu(modules_menu)
            
            self.log_activity("Modules refreshed successfully")
            
        except Exception as e:
            self.logger.error(f"Error refreshing modules: {e}")
            self.log_activity(f"Module refresh failed: {str(e)}")
    
    # Module signal handlers
    def on_module_analysis_requested(self, params):
        """Handle analysis request from a module"""
        module_name = params.get('module', 'unknown')
        self.log_activity(f"Analysis requested by {module_name}: {params}")
    
    def on_module_data_updated(self, data):
        """Handle data update from a module"""
        self.adata = data
        self.log_activity("Data updated by module")
        
        # Distribute updated data to other modules
        for module in self.loaded_modules.values():
            module.set_data(data)
    
    # Utility methods
    def log_activity(self, message):
        """Log activity to the activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if self.activity_log:
            current_text = self.activity_log.toPlainText()
            new_text = f"[{timestamp}] {message}\n{current_text}"
            self.activity_log.setText(new_text)
        self.logger.info(message)
    
    def update_memory_usage(self):
        """Update memory usage display"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"Memory: {memory_mb:.1f} MB")
        except ImportError:
            self.memory_label.setText("Memory: N/A")
    
    def show_about(self):
        """Show about dialog"""
        msg = QMessageBox()
        msg.setWindowTitle("About SingleCellStudio Modular")
        msg.setText(f"SingleCellStudio Modular {VERSION_STRING}")
        msg.setInformativeText(f"""
Modular Single Cell RNA-seq Analysis Platform

This version demonstrates a modular architecture where
analysis modules can be developed independently and
plugged into the main interface.

Loaded Modules: {len(self.loaded_modules)}
""")
        msg.exec()
    
    def closeEvent(self, event):
        """Handle close event - cleanup modules"""
        try:
            # Cleanup all modules
            for module in self.loaded_modules.values():
                module.cleanup()
            
            # Cleanup registry
            registry.cleanup_all()
            
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            event.accept()

# Main execution for testing
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    window = ModularMainWindow()
    window.show()
    
    sys.exit(app.exec()) 