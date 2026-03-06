# SingleCellStudio Professional Interface Guide

## Overview

SingleCellStudio Professional features a modern, unified interface designed for efficient single-cell RNA-seq analysis. The interface combines data import, analysis execution, and results visualization in a single window with professional-grade menus and controls.

## Interface Components

### Main Window Layout

The professional interface consists of:
- **Menu Bar**: File, Analysis, Documentation menus with keyboard shortcuts
- **Tab Interface**: Home, Analysis, Results tabs for workflow organization
- **Status Bar**: Real-time memory usage and application status
- **Progress Tracking**: Live updates during analysis execution

### Menu System

#### File Menu
- **New Project** - Start a fresh analysis session
- **Import Data (Ctrl+I)** - Load single-cell data files
- **Load Previous Results (Ctrl+L)** - Resume from saved analysis
- **Save Project (Ctrl+S)** - Save current analysis state
- **Save As** - Save project with new name
- **Export** submenu:
  - Export Data - Save analysis results
  - Export Plots - Save all generated plots
  - Export Report - Generate analysis summary
- **Recent Files** - Quick access to recent projects
- **🔄 Refresh Plots** - Reload plot display
- **Exit (Ctrl+Q)** - Close application

#### Analysis Menu
- **Run Standard Pipeline (Ctrl+R)** - Execute complete analysis
- **Quality Control** submenu - Individual QC steps
- **Normalization** submenu - Data normalization options
- **Dimensionality Reduction** submenu - PCA, UMAP, t-SNE
- **Clustering** submenu - Leiden, Louvain clustering

#### Documentation Menu
- **Getting Started** - Quick start guide
- **User Manual (F1)** - Complete documentation
- **Tutorials** - Step-by-step tutorials
- **API Reference** - Programming interface
- **Sample Data** - Download example datasets
- **Version Information** - Software details
- **About** - Application information

## Tabbed Workflow

### Home Tab
The welcome screen provides:
- **Quick Actions Panel**:
  - Import Data button
  - Load Previous Results button
  - Download Sample Data button
- **Supported Formats Information**:
  - 10X Genomics MTX folders
  - 10X Genomics H5 files
  - AnnData H5AD files
  - CSV/TSV matrices
- **System Status**:
  - Memory usage monitoring
  - Environment information
- **Activity Log**:
  - Real-time operation history
  - Detailed timestamps
  - Success/error notifications

### Analysis Tab
Optimized layout with 30% left panel, 70% right panel:

#### Left Panel - Pipeline Controls
- **Analysis Steps Overview**:
  - 10-step pipeline visualization
  - Progress indicators
  - Step-by-step status
- **Run Controls**:
  - Run Standard Analysis button
  - Stop Analysis button
  - Clear Results button

#### Right Panel - Parameter Settings
- **Quality Control Parameters**:
  - Minimum genes per cell (default: 200)
  - Minimum cells per gene (default: 3)
  - Maximum mitochondrial percentage (default: 20%)
- **Normalization Settings**:
  - Target sum for normalization (default: 10,000)
  - Number of highly variable genes (default: 2,000)
- **Dimensionality Reduction**:
  - Number of PCA components (default: 50)
  - UMAP parameters (n_neighbors, min_dist)
- **Clustering Parameters**:
  - Resolution (default: 0.5)
  - Random state for reproducibility

### Results Tab
Efficient layout with 60% plots panel, 40% controls panel:

#### Left Panel - Analysis Visualizations (60%)
Tabbed plot viewer with automatic loading:
- **Summary Tab**: 4-panel analysis overview
- **UMAP Tab**: 2D embedding with clustering
- **QC Metrics Tab**: Quality control violin plots
- **PCA Tab**: Principal components analysis
- **Generated Tabs**: Custom plots created interactively

#### Right Panel - Controls and Summary (40%)

##### Analysis Summary Section
- **Dataset Information**:
  - Number of cells and genes
  - Analysis completion status
  - Output directory path
- **Analysis Steps**:
  - Completed steps list
  - Execution times
  - Success indicators

##### Export Results Section
- **Export Data Button**: Save H5AD and CSV files
- **Export Plots Button**: Save all plots in multiple formats
- **Open Folder Button**: Access results directory

##### Interactive Plot Generation Section
- **Plot Type Selector**: UMAP, PCA, QC Metrics, Violin Plot, Heatmap, Summary
- **Color Mapping Selector**: All available metadata columns
- **Gene Selector**: For expression-based plots
- **Generate Plot Button**: Create custom visualization
- **Plot Options**:
  - Quality (DPI): 300 (default)
  - Size: 8x6 inches (default)
  - Auto-save checkbox: Enabled by default

##### Quick Actions Section
Pre-configured plot combinations:
- **UMAP + Cluster**: Standard clustering visualization
- **UMAP + Doublet Score**: Quality assessment
- **PCA + Clusters**: Dimensionality reduction overview
- **QC Overview**: Comprehensive quality metrics

## Professional Features

### Keyboard Shortcuts
- **Ctrl+I**: Import Data
- **Ctrl+L**: Load Previous Results
- **Ctrl+S**: Save Project
- **Ctrl+R**: Run Standard Analysis
- **Ctrl+Q**: Exit Application
- **F1**: User Manual

### Real-time Feedback
- **Progress Bar**: Shows during analysis execution
- **Status Messages**: Real-time operation updates
- **Memory Monitoring**: Live memory usage display
- **Activity Logging**: Detailed operation history

### Error Handling
- **Comprehensive Error Messages**: Clear problem descriptions
- **Recovery Suggestions**: Helpful troubleshooting tips
- **Graceful Degradation**: Continues operation when possible
- **Log File Generation**: Detailed error tracking

### Data Management
- **Automatic Result Organization**: Timestamped folders
- **Smart Checkpointing**: Key analysis stages saved
- **Metadata Export**: Complete analysis metrics
- **Plot Management**: Automatic loading and organization

## Workflow Examples

### Standard Analysis Workflow
1. **Start**: Launch application with `python singlecellstudio.py`
2. **Import**: File → Import Data (Ctrl+I) or Home tab quick action
3. **Configure**: Analysis tab → Adjust parameters if needed
4. **Execute**: Click "Run Standard Analysis" or use Ctrl+R
5. **Monitor**: Watch progress bar and activity log
6. **Review**: Results tab → Automatic plots loaded
7. **Explore**: Generate custom plots with different parameters
8. **Export**: Save data and plots for publication

### Resume Previous Analysis
1. **Load**: File → Load Previous Results (Ctrl+L)
2. **Browse**: Select previous results folder
3. **Review**: Automatic loading of data and plots
4. **Continue**: Generate additional plots or export results

### Custom Plot Generation
1. **Navigate**: Results tab → Interactive Plot Generation
2. **Select**: Choose plot type (UMAP, PCA, etc.)
3. **Configure**: Set color mapping and parameters
4. **Generate**: Click "Generate Plot" button
5. **Review**: New plot appears in tabbed viewer
6. **Export**: Plots automatically saved to results folder

## Tips and Best Practices

### Performance Optimization
- **Memory Management**: Monitor memory usage in status bar
- **Dataset Size**: Use subsampling for datasets >100k cells
- **Parameter Tuning**: Start with defaults, adjust based on results

### Quality Control
- **Check QC Plots**: Review cell and gene filtering results
- **Doublet Detection**: Use UMAP + Doublet Score quick action
- **Cluster Assessment**: Verify cluster resolution and quality

### Visualization
- **Plot Quality**: Use 300 DPI for publication-ready figures
- **Color Schemes**: Leverage automatic color mapping
- **Multiple Views**: Generate plots with different parameters

### Data Export
- **Format Selection**: Choose appropriate formats for downstream analysis
- **Batch Export**: Use export buttons for multiple files
- **Organization**: Results automatically organized in timestamped folders

## Troubleshooting

### Common Issues
1. **Slow Performance**: Check memory usage, close other applications
2. **Plot Display Issues**: Verify matplotlib backend, update PySide6
3. **Import Errors**: Ensure file format compatibility
4. **Analysis Failures**: Check parameter settings and data quality

### Support Resources
- **Activity Log**: Review detailed operation history
- **Log Files**: Check application logs for error details
- **Documentation**: Access help through F1 or Documentation menu
- **Error Messages**: Follow suggested troubleshooting steps

The professional interface is designed to provide a seamless, efficient workflow for single-cell RNA-seq analysis while maintaining the flexibility and power needed for advanced research applications. 