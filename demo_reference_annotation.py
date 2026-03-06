#!/usr/bin/env python3
"""
Demo script showing the new reference-based annotation method
"""

import sys
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def demo_reference_annotation():
    """Demo the reference-based annotation method"""
    print("🧬 Reference-based Cell Annotation Demo")
    print("=" * 50)
    
    try:
        from analysis.modules.annotation.cell_annotation import CellAnnotationModule
        
        # Create module
        module = CellAnnotationModule()
        print(f"✅ Module: {module.name} v{module.version}")
        print(f"📋 Available methods: {module.get_available_methods()}")
        print()
        
        # Show what makes reference-based special
        print("🔬 Reference-based Annotation Features:")
        print("• Uses 13+ comprehensive cell type signatures")
        print("• Positive AND negative marker genes for accuracy")
        print("• Confidence scoring based on signature strength")
        print("• No external dependencies required")
        print("• Works across different tissue types")
        print()
        
        # Show built-in cell types
        print("🎯 Built-in Cell Types:")
        cell_types = [
            "T cells", "CD4+ T cells", "CD8+ T cells", "Regulatory T cells",
            "B cells", "Plasma cells", "NK cells", "Monocytes", 
            "Macrophages", "Dendritic cells", "Neutrophils",
            "Endothelial cells", "Fibroblasts", "Epithelial cells"
        ]
        
        for i, ct in enumerate(cell_types, 1):
            print(f"  {i:2d}. {ct}")
        print()
        
        # Show example signature
        print("📊 Example Signature (T cells):")
        print("   Positive markers: CD3D, CD3E, CD3G, CD2, TRAC, TRBC1, TRBC2")
        print("   Negative markers: CD19, MS4A1, CD14, LYZ")
        print("   → Score = mean(positive) - 0.5 * mean(negative)")
        print()
        
        # Show advantages over basic method
        print("🚀 Improvements over Basic Method:")
        print("   ❌ Basic: Cluster 0 → Cell_type_0 (meaningless)")
        print("   ✅ Reference: Cluster 0 → T cells (biologically meaningful)")
        print("   ❌ Basic: Confidence = 0.3 (fixed low)")
        print("   ✅ Reference: Confidence = 0.1-1.0 (based on signature strength)")
        print()
        
        print("💡 How to Use:")
        print("1. Load data with clustering results")
        print("2. Select 'reference_based' or 'auto' method")
        print("3. Run analysis - no configuration needed!")
        print("4. Get meaningful cell type names automatically")
        print()
        
        print("🎯 Best For:")
        print("• PBMC data (immune cells)")
        print("• Tumor microenvironment")
        print("• General tissue analysis")
        print("• When you want automatic annotation")
        print()
        
        print("⚙️ When to Use Marker-based Instead:")
        print("• Specialized tissues (brain, liver, etc.)")
        print("• When you have tissue-specific markers")
        print("• When you need custom cell type definitions")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    success = demo_reference_annotation()
    if success:
        print("\n🎉 Demo completed! Try the reference-based method in your GUI!")
    else:
        print("\n❌ Demo failed!") 