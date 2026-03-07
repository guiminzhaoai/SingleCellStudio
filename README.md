# SingleCellStudio Professional 🔬

**Professional Single Cell RNA-seq Analysis Platform**

SingleCellStudio Professional is a comprehensive, user-friendly desktop application for single-cell RNA sequencing data analysis. Built with Python and PySide6, it provides a complete workflow from data import to publication-ready visualizations with a modern, professional interface.

## 🌟 Key Features

### ✅ **Professional Interface (v0.3.0+)**
- **Unified Professional Window**: Single-window interface with 5-tab workflow (Home, QC & Cluster, Cell Annotation, Trajectory Analysis, Cell-Cell Interaction)
- **Multi-Sample Entry Points**: Import single sample (`Ctrl+I`) or multiple samples (`Ctrl+Shift+I`) directly from the Home tab/File menu
- **Commercial-Grade Menus**: File, Analysis, and Documentation menus with keyboard shortcuts
- **Real-time Progress Tracking**: Live updates during analysis with detailed logging
- **Interactive Plot Generation**: On-demand plot creation with customizable parameters
- **Automatic Plot Generation**: Standard analysis plots created automatically after pipeline completion
- **Integrated Workflow**: Seamless data flow between analysis steps with shared annotations

### 🔬 **Complete Analysis Pipeline**
- **Quality Control**: Cell/gene filtering, mitochondrial gene analysis, doublet detection
- **Normalization**: Log normalization, scaling, highly variable gene selection
- **Dimensionality Reduction**: PCA, UMAP, t-SNE with customizable parameters
- **Clustering**: Leiden and Louvain algorithms with adjustable resolution
- **Cell Annotation**: Advanced cell type identification with multiple annotation methods
- **Trajectory Analysis**: Pseudotime, RNA Velocity, and Lineage Tracing for temporal analysis
- **Cell-Cell Interaction**: Ligand-receptor analysis, spatial proximity, and communication modeling
- **Visualization**: Publication-quality plots with multiple export formats

### 📊 **Advanced Data Management**
- **Multi-format Support**: 10X MTX folders, 10X H5 files, AnnData H5AD, CSV/TSV
- **Multi-sample Merge Support**: Combine multiple input datasets into one AnnData object with sample/batch metadata
- **Batch Metadata Tracking**: Automatic `batch` and `sample_id` labels for integration-aware analysis
- **Smart Result Organization**: Timestamped folders with structured output
- **Key Checkpoints**: Automatic saving of critical analysis stages
- **Load Previous Results**: Resume analysis from any saved checkpoint
- **Comprehensive Metadata**: CSV exports for all analysis metrics

### 🧬 **Advanced Trajectory Analysis**
- **Pseudotime Analysis**: Reconstruct developmental trajectories and temporal cell ordering
- **RNA Velocity**: Analyze RNA dynamics to infer future cell states and transition directions
- **Lineage Tracing**: Identify developmental lineages and cell fate relationships
- **Integration with Annotations**: Seamlessly use cell type annotations from clustering analysis
- **Method-Specific Parameters**: Customizable settings for each trajectory analysis method
- **Interactive Visualizations**: Real-time plots with trajectory overlays and cell type integration

### 🔗 **Cell-Cell Interaction Analysis**
- **Ligand-Receptor Analysis**: CellPhoneDB-based prediction of cellular communication
- **Spatial Proximity Analysis**: Squidpy-powered spatial interaction modeling
- **Communication Modeling**: COMMOT algorithm for communication strength quantification
- **Network Visualizations**: Interactive network plots showing communication patterns
- **Multi-dimensional Results**: Pathway enrichment, signal strength, and spatial distribution

### 🎨 **Publication-Ready Visualizations**
- **Standard Plots**: UMAP, PCA, QC metrics, summary plots generated automatically
- **Trajectory Plots**: Pseudotime gradients, velocity fields, lineage assignments
- **Interactive Generation**: Create custom plots with different color mappings
- **Quick Actions**: One-click generation of common plot combinations (UMAP + Doublet Score, PCA + Clusters)
- **Multiple Formats**: PNG (300 DPI), PDF, SVG for publications
- **Plot Management**: Automatic loading and display of generated plots

## 🚀 Quick Start

### Installation
```bash
# Create conda environment
conda create -n singlecellstudio python=3.10 -y
conda activate singlecellstudio

# Install dependencies
pip install -r requirements.txt

# Clone repository
git clone <repository-url>
cd SingleCellStudio
```

### Launch Application
```bash
# Method 1: Use the launcher script
./launch.sh

# Method 2: Direct launch
conda activate singlecellstudio
python singlecellstudio.py

# Method 3: From source
python src/main.py
```

### Professional Workflow
1. **📁 Import Single or Multiple Samples** → Use `Ctrl+I` (single) or `Ctrl+Shift+I` (multi-sample)
2. **🧩 (Optional) Harmony Integration** → Enable Harmony in QC & Cluster parameters when `batch` metadata is available
3. **🔬 Run QC & Clustering** → Click "Run Standard Analysis" with customizable parameters
4. **🏷️ Annotate Cell Types** → Advanced cell type identification and annotation
5. **🧬 Trajectory Analysis** → Run trajectory methods on integrated analysis results
6. **🔗 Cell-Cell Interaction** → Run interaction analysis on integrated analysis results
7. **📊 View Results** → Automatic plot generation and results summary
8. **💾 Export Results** → Export AnnData, plots, and PDF analysis summary report

## 📁 Project Structure

```
SingleCellStudio/
├── singlecellstudio.py          # 🚀 Main entry point
├── src/                         # Source code
│   ├── main.py                 # Application launcher
│   ├── data/                   # Data loading and validation
│   ├── analysis/               # Analysis pipeline
│   ├── visualization/          # Plotting system
│   ├── gui/                    # Professional user interface
│   │   └── professional_main_window.py  # Main GUI
│   └── utils/                  # Utility functions
├── docs/                        # 📚 Documentation
├── tests/                       # Test suite
├── examples/                    # Sample data and scripts
├── requirements.txt             # Dependencies
├── launch.sh                    # Quick launch script
└── README.md                    # This file
```

## 📁 Results Structure

All analysis results are automatically organized in timestamped folders:

```
results_[filename]_[timestamp]/
├── intermediate_data/
│   ├── normalize_data.h5ad      # After normalization
│   └── clustering.h5ad          # Final analysis with clusters
├── metadata/
│   ├── analysis_summary.csv     # Complete analysis overview
│   ├── cell_filtering_stats.csv # QC metrics
│   ├── cluster_statistics.csv   # Clustering results
│   ├── pca_coordinates.csv      # PCA embeddings
│   └── umap_coordinates.csv     # UMAP embeddings
├── plots/
│   ├── summary_[timestamp].png  # 4-panel analysis overview
│   ├── umap_[timestamp].png     # UMAP clustering plot
│   ├── qc_[timestamp].png       # Quality control metrics
│   ├── pca_[timestamp].png      # PCA plot
│   └── custom_[type]_[timestamp].png  # Interactive plots
└── logs/
    └── execution_log.csv        # Detailed analysis log
```

## 🎯 Supported Data Formats

### Input Formats
- **10X Genomics MTX**: Folder with `matrix.mtx.gz`, `barcodes.tsv.gz`, `features.tsv.gz`
- **10X Genomics H5**: `filtered_feature_bc_matrix.h5`
- **AnnData H5AD**: `data.h5ad` (for loading previous results)
- **CSV/TSV**: Gene expression matrices with optional compression

### Output Formats
- **Analysis Data**: H5AD format for key checkpoints
- **Metadata**: CSV format for all metrics and coordinates
- **Plots**: PNG (300 DPI), PDF, SVG for publications

## 🔧 Analysis Pipeline

### Standard Pipeline (11 steps when Harmony is enabled)
1. **Quality Control** - Calculate QC metrics (genes/cell, counts/cell, MT%, doublet scores)
2. **Cell Filtering** - Remove low-quality cells based on QC thresholds
3. **Gene Filtering** - Remove lowly expressed genes
4. **Normalization** - Log normalization with target sum scaling
5. **Variable Gene Selection** - Identify highly variable genes
6. **Data Scaling** - Z-score normalization for downstream analysis
7. **PCA** - Principal component analysis for dimensionality reduction
8. **Harmony Integration (Optional)** - Batch-effect integration in PCA space for multi-sample datasets
9. **Neighbor Graph** - k-nearest neighbor graph construction (uses Harmony embedding when enabled)
10. **UMAP** - 2D embedding generation for visualization
11. **Clustering** - Leiden clustering for cell type identification

### Customizable Parameters
- **Cell Filtering**: Min genes per cell (200), min cells per gene (3)
- **Feature Selection**: Number of highly variable genes (2000)
- **Clustering**: Resolution parameter (0.5) for granularity control
- **Dimensionality**: Number of PCA components (40 default in professional UI)
- **Integration**: Optional Harmony batch integration toggle (enabled when `batch` labels exist)

## 📈 Professional Visualization Features

### Automatic Plot Generation
After analysis completion, the following plots are automatically generated:
- **Summary Plot**: 4-panel overview (UMAP, gene counts, total counts, cluster sizes)
- **UMAP Plot**: 2D embedding with Leiden clustering
- **QC Plot**: Quality control metrics violin plots
- **PCA Plot**: Principal components with cluster coloring

### Interactive Plot Generation
- **Plot Types**: UMAP, PCA, QC Metrics, Violin Plot, Heatmap, Summary
- **Color Mapping**: Any metadata column (clusters, QC metrics, gene expression)
- **Gene Selection**: Custom gene lists for expression plots
- **Quality Settings**: Adjustable DPI (300) and plot size (8x6)
- **Quick Actions**: Pre-configured plot combinations
  - UMAP + Cluster: Standard clustering visualization
  - UMAP + Doublet Score: Quality control assessment
  - PCA + Clusters: Dimensionality reduction overview
  - QC Overview: Comprehensive quality metrics

### Export Options
- **Export Data**: H5AD/metadata outputs for downstream analysis
- **Export Plots**: Individual or batch export in multiple formats
- **Export PDF Report**: One-click PDF summary generation from the results panel or File → Export
- **Open Folder**: Direct access to results directory

## 💻 System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **RAM**: 8GB (16GB+ recommended for large datasets >50k cells)
- **Storage**: 2GB free space + 2x dataset size for intermediate files
- **Python**: 3.8+ (3.10 recommended)

### Key Dependencies
- **Core**: numpy, pandas, scipy, matplotlib, seaborn
- **Single-cell**: scanpy>=1.9.0, anndata>=0.8.0
- **Clustering**: umap-learn, leidenalg, python-igraph
- **GUI**: PySide6
- **Data**: h5py, tables

## 🧪 Example Usage

### Test with Sample Data
```bash
# Download sample data (if available)
cd examples
python download_sample_data.py

# Launch application
cd ..
python singlecellstudio.py

# In GUI:
# 1. File → Import Data (Ctrl+I)
# 2. Select examples/sample_data/filtered_feature_bc_matrix.h5
# 3. Analysis tab → Run Standard Analysis
# 4. Results tab → View automatic plots and generate custom ones
```

### Expected Results
- **Dataset**: ~12,000 cells, ~38,000 genes
- **Analysis Time**: ~30 seconds on modern hardware
- **Clusters**: 10-15 distinct cell populations
- **Output Size**: ~50MB including all plots and metadata

## 🔧 Professional Interface Features

### Menu System
- **File Menu**: New Project, Import Data (Ctrl+I), Import Multiple Samples (Ctrl+Shift+I), Load Previous Results (Ctrl+L), Save Project (Ctrl+S), Export options, Recent files
- **Analysis Menu**: Run Standard Pipeline (Ctrl+R), Individual analysis steps, Parameter customization
- **Documentation Menu**: Getting Started, User Manual (F1), Tutorials, API Reference, About

### Tabbed Workflow
- **Home Tab**: Welcome screen, quick actions (including multi-sample import), system status, recent activity
- **QC & Cluster Tab**: Standard analysis pipeline controls and parameter settings (including optional Harmony integration)
- **Cell Annotation Tab**: Advanced cell type identification with multiple annotation methods
- **Trajectory Analysis Tab**: Temporal analysis controls and trajectory visualizations
- **Cell-Cell Interaction Tab**: Ligand-receptor/spatial/communication interaction analysis

### Professional Features
- **Keyboard Shortcuts**: Standard shortcuts for common operations
- **Progress Tracking**: Real-time analysis progress with detailed steps
- **Memory Monitoring**: Live memory usage display
- **Error Handling**: Comprehensive error messages and recovery options
- **Activity Logging**: Detailed operation history with timestamps

## 📚 Documentation

### Getting Started
- Installation guide with conda environment setup
- First analysis walkthrough with sample data
- Interface overview and navigation guide

### User Manual
- Complete feature documentation
- Analysis parameter explanations
- Troubleshooting guide

### Development Plans
- [Modular Architecture Plan](docs/MODULAR_ARCHITECTURE_PLAN.md) - Future roadmap for advanced analysis modules
- [Modular Development Best Practices](docs/MODULAR_DEVELOPMENT_BEST_PRACTICES.md) - Proven development workflow for new modules
- [Migration Summary](MIGRATION_SUMMARY.md) - PyQt6 to PySide6 migration details

### API Reference
- Python API for programmatic access
- Custom analysis pipeline development
- Plugin development guide

## 🐛 Troubleshooting

### Common Issues
1. **Import Errors**: Ensure conda environment is activated and dependencies installed
2. **Memory Issues**: Close other applications, increase system RAM, or use smaller datasets
3. **Plot Display**: Check matplotlib backend, update PySide6
4. **File Loading**: Verify file format and integrity

### Support
- Check documentation for common solutions
- Review log files in the application for detailed error messages
- Ensure all dependencies are up to date

## 📄 License

SingleCellStudio Professional is commercial software. Please contact info@singlecellstudio.com for licensing information.

## 🔄 Version History

### v0.3.0+ (Current)
- ✅ Professional unified interface with 5-tab workflow
- ✅ Multi-sample import and merge workflow
- ✅ Optional Harmony integration in standard pipeline
- ✅ Export PDF report from results summary
- ✅ Advanced cell type annotation system
- ✅ Trajectory analysis (Pseudotime, RNA Velocity, Lineage Tracing)
- ✅ Integrated workflow with seamless data sharing
- ✅ Automatic plot generation
- ✅ Interactive plot creation
- ✅ Load previous results functionality
- ✅ Comprehensive result organization
- ✅ Real-time progress tracking
- ✅ Professional QSS styling

### v0.1.0
- Basic analysis pipeline
- Simple GUI interface
- Standard visualization outputs

---

**SingleCellStudio Professional** - Making single-cell analysis accessible to everyone 🧬 