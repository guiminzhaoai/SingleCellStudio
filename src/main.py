#!/usr/bin/env python3
"""
SingleCellStudio - Main Application Entry Point
Commercial Single Cell Transcriptome Analysis Software
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

# Import version information
from version import __version__, VERSION_STRING, get_full_version_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('singlecellstudio.log')
    ]
)

logger = logging.getLogger(__name__)

def check_system_requirements():
    """Check if system meets minimum requirements"""
    import platform
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error(f"Python 3.8+ required, found {sys.version}")
        return False
    
    # Check operating system
    if platform.system() != "Windows":
        logger.warning(f"SingleCellStudio is optimized for Windows, detected {platform.system()}")
    
    # Check available memory (basic check)
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < 8:
            logger.warning(f"Low memory detected: {memory_gb:.1f}GB. 16GB+ recommended.")
    except ImportError:
        logger.info("psutil not available, skipping memory check")
    
    return True

def setup_environment():
    """Setup the application environment"""
    # Set Qt application attributes (these are for PyQt5 compatibility)
    # In PySide6, high DPI scaling is enabled by default
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    # Set matplotlib backend - try different Qt backends
    try:
        import matplotlib
        # Try different Qt backends in order of preference
        backends_to_try = ['qtagg', 'qt5agg', 'tkagg', 'agg']
        backend_set = False
        
        for backend in backends_to_try:
            try:
                matplotlib.use(backend)
                logger.info(f"Using {backend} matplotlib backend")
                backend_set = True
                break
            except ValueError:
                continue
        
        if not backend_set:
            matplotlib.use('agg')  # Final fallback
            logger.warning("Using Agg matplotlib backend (no GUI plots)")
            
    except ImportError:
        logger.warning("Matplotlib not available")
    
    logger.info("Environment setup completed")

def create_gui_application():
    """Create and configure the GUI application"""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QIcon
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("SingleCellStudio")
        app.setApplicationVersion(__version__)
        app.setOrganizationName("SingleCellStudio Inc.")
        app.setOrganizationDomain("singlecellstudio.com")
        
        # Note: High DPI scaling is enabled by default in PySide6
        # The AA_EnableHighDpiScaling and AA_UseHighDpiPixmaps attributes
        # were removed in PySide6 as they're no longer needed
        
        # Set application icon
        icon_path = src_dir / "resources" / "icons" / "app_icon.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        logger.info("GUI application created successfully")
        return app
        
    except ImportError as e:
        logger.error(f"Failed to import PySide6: {e}")
        logger.error("Please install PySide6: pip install PySide6")
        return None

def main_gui():
    """Main GUI application entry point"""
    logger.info(f"Starting SingleCellStudio {VERSION_STRING}")
    
    # Check system requirements
    if not check_system_requirements():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Create GUI application
    app = create_gui_application()
    if app is None:
        sys.exit(1)
    
    try:
        # Import and create professional main window
        from gui.professional_main_window import ProfessionalMainWindow
        
        main_window = ProfessionalMainWindow()
        main_window.show()
        
        logger.info("Professional main window created and shown")
        
        # Start the event loop
        sys.exit(app.exec())
        
    except ImportError as e:
        logger.error(f"Failed to import professional main window: {e}")
        logger.error("Please ensure all dependencies are installed")
        
        # Show error message
        try:
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("SingleCellStudio - Error")
            msg.setText(f"SingleCellStudio {VERSION_STRING}\n\nFailed to launch application.")
            msg.setInformativeText(f"Error: {e}\n\nPlease check that all dependencies are installed.")
            msg.exec()
        except:
            print(f"Failed to launch SingleCellStudio: {e}")
        
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

def main_cli():
    """Command-line interface entry point"""
    logger.info(f"SingleCellStudio CLI {VERSION_STRING}")
    
    # Basic CLI functionality for testing
    print(f"SingleCellStudio {VERSION_STRING}")
    print("Command-line interface is under development")
    print("\nFor GUI mode, run: singlecellstudio-gui")
    
    # Show version info
    version_info = get_full_version_info()
    print(f"\nVersion Information:")
    for key, value in version_info.items():
        print(f"  {key}: {value}")

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="SingleCellStudio - Commercial Single Cell Transcriptome Analysis Software",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  singlecellstudio --gui          # Launch GUI interface
  singlecellstudio --version      # Show version information
  singlecellstudio --check        # Check system requirements
        """
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"SingleCellStudio {VERSION_STRING}"
    )
    
    parser.add_argument(
        "--gui", 
        action="store_true", 
        help="Launch GUI interface (default)"
    )
    
    parser.add_argument(
        "--cli", 
        action="store_true", 
        help="Use command-line interface"
    )
    
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Check system requirements"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Check system requirements
    if args.check:
        if check_system_requirements():
            print("✓ System requirements check passed")
            sys.exit(0)
        else:
            print("✗ System requirements check failed")
            sys.exit(1)
    
    # Choose interface
    if args.cli:
        main_cli()
    else:
        # Default to GUI
        main_gui()

if __name__ == "__main__":
    main() 