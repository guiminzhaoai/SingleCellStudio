#!/usr/bin/env python3
"""
SingleCellStudio - Professional Single Cell RNA-seq Analysis Platform
Main Application Launcher

This is the primary entry point for SingleCellStudio Professional Edition.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def main():
    """Main entry point for SingleCellStudio Professional"""
    print("🔬 SingleCellStudio Professional Edition")
    print("=" * 50)
    
    try:
        # Import main function from src
        from main import main_gui
        
        # Launch the professional GUI
        main_gui()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\n💡 Installation Help:")
        print("1. Make sure you're in the correct conda environment:")
        print("   conda activate singlecellstudio")
        print("2. Install missing dependencies:")
        print("   pip install -r requirements.txt")
        print("3. For PySide6 issues, try:")
        print("   pip install PySide6")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error launching SingleCellStudio: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 