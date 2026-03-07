#!/usr/bin/env python3
"""
SingleCellStudio v0.3.0 Pre-Release Test Script

Quick test to verify all pre-release modifications work correctly.
This script will test the basic functionality without running the full GUI.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all imports work correctly"""
    print("🔍 Testing imports...")
    
    try:
        # Test main window import
        from src.gui.professional_main_window import ProfessionalMainWindow
        print("✅ Professional main window import: OK")
        
        # Test other critical imports
        from src.gui.professional_main_window import AnalysisWorker
        print("✅ Analysis worker import: OK")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "src/gui/professional_main_window.py",
        "src/gui/default.qss",
        "examples/sample_data/filtered_feature_bc_matrix.h5",
        "docs/CELL_INTERACTION_ANALYSIS_GUIDE.md",
        "docs/TRAJECTORY_ANALYSIS_GUIDE.md",
        "docs/PRE_RELEASE_CHECKLIST.md",
        "docs/VIDEO_PRODUCTION_GUIDE.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}: OK")
        else:
            print(f"❌ {file_path}: MISSING")
            all_exist = False
    
    return all_exist

def test_class_structure():
    """Test that the main window class has all required methods"""
    print("\n🔧 Testing class structure...")
    
    try:
        from src.gui.professional_main_window import ProfessionalMainWindow
        
        # Required methods from our modifications
        required_methods = [
            'load_sample_data',
            '_load_data_from_path', 
            '_update_data_display',
            'open_examples_folder',
            'open_documentation_folder',
            'show_interaction_guide',
            'show_trajectory_guide'
        ]
        
        all_methods_exist = True
        for method_name in required_methods:
            if hasattr(ProfessionalMainWindow, method_name):
                print(f"✅ Method {method_name}: OK")
            else:
                print(f"❌ Method {method_name}: MISSING")
                all_methods_exist = False
        
        return all_methods_exist
        
    except Exception as e:
        print(f"❌ Class structure test failed: {e}")
        return False

def test_syntax():
    """Test Python syntax of main files"""
    print("\n🐍 Testing Python syntax...")
    
    try:
        import py_compile
        
        files_to_check = [
            "src/gui/professional_main_window.py"
        ]
        
        all_syntax_ok = True
        for file_path in files_to_check:
            try:
                py_compile.compile(file_path, doraise=True)
                print(f"✅ {file_path}: Syntax OK")
            except py_compile.PyCompileError as e:
                print(f"❌ {file_path}: Syntax Error - {e}")
                all_syntax_ok = False
        
        return all_syntax_ok
        
    except Exception as e:
        print(f"❌ Syntax test failed: {e}")
        return False

def main():
    """Run all pre-release tests"""
    print("🚀 SingleCellStudio v0.3.0 Pre-Release Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("File Structure Test", test_file_structure), 
        ("Class Structure Test", test_class_structure),
        ("Syntax Test", test_syntax)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Ready for release! 🚀")
        print("\nNext steps:")
        print("1. 🔧 Run: python src/gui/professional_main_window.py")
        print("2. 🧪 Test sample data loading")
        print("3. 🎬 Start video recording")
    else:
        print("⚠️  Some tests failed. Please fix issues before release.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 