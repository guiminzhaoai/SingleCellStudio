# Cell Annotation Methods Guide

## Overview
SingleCellStudio provides multiple methods for annotating cell types in single-cell RNA-seq data. Each method has different strengths and use cases.

## Available Methods

### 1. Reference-based Annotation (NEW!)
**What it does:** Automatic annotation using comprehensive cell type signatures
- Uses positive and negative marker gene signatures for 13+ cell types
- Calculates signature scores by comparing positive vs negative markers
- Provides confidence scores based on signature strength and uniqueness
- No external dependencies required

**Built-in Cell Types:**
- T cells (general), CD4+ T cells, CD8+ T cells, Regulatory T cells
- B cells, Plasma cells
- NK cells, Monocytes, Macrophages, Dendritic cells, Neutrophils
- Endothelial cells, Fibroblasts, Epithelial cells

**How it works:**
1. For each cluster, calculates expression of positive markers
2. Subtracts expression of negative markers (to avoid misclassification)
3. Assigns cell type with highest signature score
4. Confidence based on margin between best and second-best scores

**Pros:**
- Fully automatic - no user input needed
- Sophisticated scoring using positive + negative markers
- High confidence when signatures are clear
- Works across different tissue types
- No external dependencies

**Cons:**
- Limited to built-in cell types
- May not work well for specialized tissues
- Requires good gene coverage

### 2. Marker-based Annotation
**What it does:** Uses known marker genes to identify cell types
- Calculates marker gene expression for each cluster
- Assigns cell types based on highest-expressing markers
- Provides confidence scores based on expression strength

**Default Marker Genes:**
```json
{
    "T cells": ["CD3D", "CD3E", "CD3G", "CD2"],
    "CD4+ T cells": ["CD3D", "CD4", "IL7R"],
    "CD8+ T cells": ["CD3D", "CD8A", "CD8B"],
    "B cells": ["CD19", "MS4A1", "CD79A", "CD79B"],
    "NK cells": ["GNLY", "NKG7", "KLRD1", "NCAM1"],
    "Monocytes": ["CD14", "LYZ", "S100A9", "FCGR3A"],
    "Dendritic cells": ["FCER1A", "CST3", "CLEC9A"],
    "Plasma cells": ["IGHG1", "MZB1", "SDC1", "CD38"],
    "Macrophages": ["CD68", "CD163", "MSR1"],
    "Neutrophils": ["FCGR3B", "CEACAM8", "CSF3R"]
}
```

**Custom Markers:**
You can provide your own marker genes in JSON format:
```json
{
    "Hepatocytes": ["ALB", "AFP", "APOA1"],
    "Kupffer cells": ["CD68", "CLEC4F", "VSIG4"],
    "Stellate cells": ["ACTA2", "COL1A1", "PDGFRB"]
}
```

**Pros:**
- Biologically meaningful
- Customizable
- Good confidence scores
- Works with any tissue type

**Cons:**
- Requires knowledge of marker genes
- Limited by marker gene availability in dataset
- May miss rare cell types

### 3. CellTypist Annotation
**What it does:** Automated annotation using pre-trained models
- Uses machine learning models trained on reference datasets
- Provides high-confidence automated annotations
- Supports multiple tissue types and species

**Current Status:** 
- Integration in progress
- Requires specific data preprocessing
- Falls back to marker-based method

**Future Features:**
- Multiple pre-trained models
- Species-specific annotations
- Tissue-specific models
- Confidence scoring

### 4. Auto Method
**What it does:** Automatically selects the best available method
- Tries CellTypist first (if available)
- Falls back to reference-based annotation (recommended)
- Uses marker-based annotation if reference-based fails

## How to Use

### In the GUI:
1. Load your data with clustering results
2. Go to Analysis → Cell Annotation tab
3. Select your preferred method
4. For marker-based: optionally enable custom markers
5. Set confidence threshold
6. Click "Run Analysis"
7. View results and create visualizations

### Custom Marker Genes:
1. Check "Use Custom Marker Genes"
2. Edit the JSON in the text area
3. Use this format:
   ```json
   {
       "Cell Type Name": ["GENE1", "GENE2", "GENE3"],
       "Another Cell Type": ["GENE4", "GENE5"]
   }
   ```
4. Make sure gene names match your data exactly

## Tips for Better Results

### Data Requirements:
- Clustering results must be present (leiden clustering)
- Gene expression data should be available
- For marker-based: ensure marker genes are present in your dataset

### Choosing Methods:
- **Reference-based**: Best for most cases - automatic with good coverage
- **Marker-based**: When you have specific marker genes for your tissue
- **CellTypist**: For automated, high-confidence annotations (when available)
- **Auto**: Let the system choose the best method (recommended)

### Improving Marker-based Results:
1. Use tissue-specific marker genes
2. Include multiple markers per cell type
3. Verify marker genes are expressed in your dataset
4. Consider cell type hierarchy (e.g., T cells → CD4+ T cells)

### Confidence Scores:
- **0.1-0.4**: Low confidence 
- **0.4-0.7**: Moderate confidence 
- **0.7-1.0**: High confidence (strong signature match)

## Troubleshooting

### Common Issues:
1. **"No clustering results found"**: Run clustering analysis first
2. **"Marker genes not found"**: Check gene names match your data
3. **"Low confidence scores"**: Try different marker genes or methods
4. **"CellTypist not available"**: Install celltypist package or use other methods

### Getting Better Results:
1. Ensure high-quality clustering
2. Use appropriate marker genes for your tissue type
3. Consider cell type abundance in your sample
4. Validate results with known biology

## Future Enhancements
- Full CellTypist integration
- Interactive marker gene selection
- Cell type hierarchy support
- Batch annotation capabilities
- Custom model training 