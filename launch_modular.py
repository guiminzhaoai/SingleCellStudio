#!/usr/bin/env python3
"""
SingleCellStudio Modular Edition Launcher

Launch the modular version of SingleCellStudio that supports
dynamic module loading and plugin architecture.
"""

import os
import sys
from pathlib import Path

def main():
    """Launch SingleCellStudio in modular mode"""
    
    print("🔬 SingleCellStudio - Modular Edition")
    print("=" * 50)
    
    # Set environment variable to use modular version
    os.environ['SINGLECELLSTUDIO_MODULAR'] = 'true'
    
    # Add src directory to Python path
    src_dir = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_dir))
    
    try:
        # Import and run main function
        from main import main_gui
        
        print("🚀 Launching modular interface...")
        print("✨ Features:")
        print("   • Dynamic module loading")
        print("   • Plugin architecture") 
        print("   • Independent module development")
        print("   • Auto-discovery of new modules")
        print()
        
        # Launch the modular GUI
        main_gui()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\n💡 Solution:")
        print("1. Make sure you're in the correct environment")
        print("2. Install missing dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error launching modular version: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 