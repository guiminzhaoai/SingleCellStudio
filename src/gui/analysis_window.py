"""
SingleCellStudio Analysis Window

Analysis interface shown after data import, providing access to clustering,
visualization, and other analysis functions.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QMessageBox, QMenuBar, QStatusBar,
    QTabWidget, QGroupBox, QGridLayout, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QProgressBar, QScrollArea,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTableWidget,
    QTableWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QAction, QPixmap

try:
    import anndata as ad
    import pandas as pd
    import numpy as np
    from analysis import run_standard_pipeline
    from visualization.matplotlib_backend import MatplotlibPlotter
    ANALYSIS_AVAILABLE = True
    VISUALIZATION_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False
    VISUALIZATION_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

class AnalysisWorker(QThread):
    """Worker thread for running analysis pipeline"""
    
    progress_updated = Signal(int, str)
    analysis_completed = Signal(object, dict)
    analysis_failed = Signal(str)
    
    def __init__(self, adata, pipeline_params=None, output_dir=None):
        super().__init__()
        self.adata = adata
        self.pipeline_params = pipeline_params or {}
        self.output_dir = output_dir
    
    def run(self):
        """Run the analysis pipeline"""
        try:
            self.progress_updated.emit(0, "Starting analysis pipeline...")
            
            if not ANALYSIS_AVAILABLE:
                raise ImportError("Analysis modules not available")
            
            # Run the standard pipeline with output directory
            result_adata, results = run_standard_pipeline(
                self.adata, 
                output_dir=self.output_dir,
                **self.pipeline_params
            )
            
            self.progress_updated.emit(100, "Analysis completed successfully!")
            self.analysis_completed.emit(result_adata, results)
            
        except Exception as e:
            self.analysis_failed.emit(str(e))

class AnalysisWindow(QMainWindow):
    """Analysis interface window"""
    
    def __init__(self, adata: ad.AnnData, parent=None, input_file_path=None):
        super().__init__(parent)
        self.adata = adata
        self.analysis_adata = None
        self.analysis_results = None
        self.worker = None
        self.input_file_path = input_file_path
        
        # Set up output directory based on input file location
        self.output_dir = self._setup_output_directory()
        
        self.init_ui()
    
    def _setup_output_directory(self):
        """
        Set up output directory based on input file location
        
        Returns:
        --------
        Path : Output directory for results
        """
        from datetime import datetime
        
        if self.input_file_path:
            # Create results folder next to input file
            input_path = Path(self.input_file_path)
            base_dir = input_path.parent
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = base_dir / f"results_{input_path.stem}_{timestamp}"
        else:
            # Create results folder in current directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(f"results/analysis_results_{timestamp}")
        
        # Create directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Output directory set up: {output_dir.absolute()}")
        return output_dir
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("SingleCellStudio - Analysis Interface")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # Data info header
        info_layout = QHBoxLayout()
        
        data_info = QLabel(f"📊 Dataset: {self.adata.n_obs:,} cells × {self.adata.n_vars:,} genes")
        data_info.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(data_info)
        
        info_layout.addStretch()
        
        # Analysis status
        self.status_label = QLabel("Ready for analysis")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        info_layout.addWidget(self.status_label)
        
        main_layout.addLayout(info_layout)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Analysis controls
        left_panel = self.create_analysis_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Results and visualization
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 1)  # Left panel
        splitter.setStretchFactor(1, 2)  # Right panel (larger)
        
        main_layout.addWidget(splitter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        central_widget.setLayout(main_layout)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
        
        # Apply styling
        self.apply_styling()
    
    def create_analysis_panel(self):
        """Create the left analysis control panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Analysis Pipeline Section
        pipeline_group = QGroupBox("🔬 Analysis Pipeline")
        pipeline_layout = QVBoxLayout()
        
        # Quick analysis button
        quick_btn = QPushButton("🚀 Run Standard Analysis")
        quick_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        quick_btn.clicked.connect(self.run_standard_analysis)
        pipeline_layout.addWidget(quick_btn)
        
        # Analysis steps info
        steps_info = QTextEdit()
        steps_info.setMaximumHeight(200)
        steps_info.setReadOnly(True)
        steps_info.setText("""Standard Analysis Pipeline:

1. 🔍 Quality Control - Calculate QC metrics
2. 🧹 Cell Filtering - Remove low-quality cells  
3. 🧬 Gene Filtering - Remove lowly expressed genes
4. 📊 Normalization - Log normalize expression
5. 🔬 Variable Genes - Find highly variable genes
6. ⚖️ Scaling - Z-score normalize data
7. 📉 PCA - Principal component analysis
8. 🕸️ Neighbors - Build k-nearest neighbor graph
9. 🗺️ UMAP - Generate 2D embedding
10. 🎯 Clustering - Leiden clustering algorithm

This will take 1-2 minutes depending on dataset size.""")
        pipeline_layout.addWidget(steps_info)
        
        pipeline_group.setLayout(pipeline_layout)
        layout.addWidget(pipeline_group)
        
        # Parameters section
        params_group = QGroupBox("⚙️ Parameters")
        params_layout = QGridLayout()
        
        # Min cells per gene
        params_layout.addWidget(QLabel("Min cells per gene:"), 0, 0)
        self.min_cells_spin = QSpinBox()
        self.min_cells_spin.setRange(1, 100)
        self.min_cells_spin.setValue(3)
        params_layout.addWidget(self.min_cells_spin, 0, 1)
        
        # Min genes per cell
        params_layout.addWidget(QLabel("Min genes per cell:"), 1, 0)
        self.min_genes_spin = QSpinBox()
        self.min_genes_spin.setRange(100, 10000)
        self.min_genes_spin.setValue(200)
        params_layout.addWidget(self.min_genes_spin, 1, 1)
        
        # Max mitochondrial %
        params_layout.addWidget(QLabel("Max mitochondrial %:"), 2, 0)
        self.max_mito_spin = QDoubleSpinBox()
        self.max_mito_spin.setRange(5.0, 50.0)
        self.max_mito_spin.setValue(20.0)
        self.max_mito_spin.setSuffix("%")
        params_layout.addWidget(self.max_mito_spin, 2, 1)
        
        # Number of variable genes
        params_layout.addWidget(QLabel("Variable genes:"), 3, 0)
        self.n_top_genes_spin = QSpinBox()
        self.n_top_genes_spin.setRange(1000, 10000)
        self.n_top_genes_spin.setValue(2000)
        params_layout.addWidget(self.n_top_genes_spin, 3, 1)
        
        # Clustering resolution
        params_layout.addWidget(QLabel("Clustering resolution:"), 4, 0)
        self.resolution_spin = QDoubleSpinBox()
        self.resolution_spin.setRange(0.1, 2.0)
        self.resolution_spin.setValue(0.5)
        self.resolution_spin.setSingleStep(0.1)
        params_layout.addWidget(self.resolution_spin, 4, 1)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        
        return panel
    
    def create_results_panel(self):
        """Create the right results panel"""
        panel = QTabWidget()
        
        # Results Overview Tab
        overview_tab = QWidget()
        overview_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setText("""📋 Analysis Results

No analysis has been run yet. Click "Run Standard Analysis" to begin.

After analysis, you will see:
• Quality control metrics
• Filtering statistics  
• Normalization results
• PCA variance explained
• UMAP coordinates
• Cluster assignments
• Execution timing

The analysis will automatically:
1. Process your data through the standard pipeline
2. Generate quality control plots
3. Create UMAP visualization
4. Identify cell clusters
5. Provide summary statistics""")
        overview_layout.addWidget(self.results_text)
        
        overview_tab.setLayout(overview_layout)
        panel.addTab(overview_tab, "📊 Overview")
        
        # Data Table Tab
        table_tab = QWidget()
        table_layout = QVBoxLayout()
        
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        table_layout.addWidget(self.data_table)
        
        table_tab.setLayout(table_layout)
        panel.addTab(table_tab, "📋 Data")
        
        # Visualization Tab
        if VISUALIZATION_AVAILABLE:
            self.viz_widget = None  # Will be created after analysis
            viz_tab = QWidget()
            viz_layout = QVBoxLayout()
            
            self.viz_placeholder = QLabel("🎨 Visualization plots will appear here after analysis")
            self.viz_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.viz_placeholder.setStyleSheet("color: #666; font-size: 14px; padding: 50px;")
            viz_layout.addWidget(self.viz_placeholder)
            
            viz_tab.setLayout(viz_layout)
            self.viz_tab = viz_tab
            self.viz_layout = viz_layout
        else:
            viz_tab = QWidget()
            viz_layout = QVBoxLayout()
            
            viz_info = QLabel("🎨 Visualization not available - missing dependencies")
            viz_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            viz_info.setStyleSheet("color: #666; font-size: 14px; padding: 50px;")
            viz_layout.addWidget(viz_info)
            
            viz_tab.setLayout(viz_layout)
        
        panel.addTab(viz_tab, "🎨 Plots")
        
        return panel
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # Analysis menu
        analysis_menu = menubar.addMenu('Analysis')
        
        run_action = QAction('Run Standard Pipeline', self)
        run_action.setShortcut('Ctrl+R')
        run_action.triggered.connect(self.run_standard_analysis)
        analysis_menu.addAction(run_action)
        
        # Export menu
        export_menu = menubar.addMenu('Export')
        
        export_results_action = QAction('Export Results...', self)
        export_results_action.triggered.connect(self.export_results)
        export_menu.addAction(export_results_action)
    
    def create_status_bar(self):
        """Create the status bar"""
        status_bar = self.statusBar()
        status_bar.showMessage("Ready for analysis")
    
    def apply_styling(self):
        """Apply styling to the window"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #007bff;
            }
        """)
    
    def run_standard_analysis(self):
        """Run the standard analysis pipeline"""
        if not ANALYSIS_AVAILABLE:
            QMessageBox.warning(
                self,
                "Analysis Not Available",
                "Analysis modules are not available. Please ensure all dependencies are installed."
            )
            return
        
        # Get parameters
        params = {
            'min_cells': self.min_cells_spin.value(),
            'min_genes': self.min_genes_spin.value(),
            'max_mito_percent': self.max_mito_spin.value(),
            'n_top_genes': self.n_top_genes_spin.value(),
            'resolution': self.resolution_spin.value()
        }
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Running analysis...")
        
        # Start analysis in worker thread
        self.worker = AnalysisWorker(self.adata, params, self.output_dir)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.analysis_completed.connect(self.analysis_completed)
        self.worker.analysis_failed.connect(self.analysis_failed)
        self.worker.start()
    
    def update_progress(self, value, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        self.statusBar().showMessage(message)
    
    def analysis_completed(self, adata, results):
        """Handle completed analysis"""
        self.analysis_adata = adata
        self.analysis_results = results
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        self.status_label.setText("Analysis completed successfully!")
        
        # Update results display
        self.update_results_display()
        
        # Create visualization plots - use QTimer to ensure it runs in main thread
        QTimer.singleShot(100, self.create_visualizations)
        
        # Show completion message
        QMessageBox.information(
            self,
            "Analysis Complete",
            f"Standard analysis pipeline completed successfully!\n\n"
            f"Results:\n"
            f"• {adata.n_obs:,} cells after filtering\n"
            f"• {adata.n_vars:,} genes after filtering\n"
            f"• {len(set(adata.obs['leiden']))} clusters identified\n\n"
            f"Check the tabs above to explore your results and visualizations."
        )
    
    def analysis_failed(self, error_message):
        """Handle failed analysis"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Analysis failed")
        
        QMessageBox.critical(
            self,
            "Analysis Failed",
            f"The analysis pipeline failed with error:\n\n{error_message}"
        )
    
    def update_results_display(self):
        """Update the results display with analysis results"""
        if self.analysis_results is None:
            return
        
        # Update results text
        results_text = "📋 Analysis Results\n\n"
        
        # Add execution summary
        if 'execution_time' in self.analysis_results:
            results_text += f"⏱️ Total execution time: {self.analysis_results['execution_time']:.1f}s\n\n"
        
        # Add step details
        if 'step_results' in self.analysis_results:
            results_text += "📊 Pipeline Steps:\n\n"
            for step_name, step_result in self.analysis_results['step_results'].items():
                results_text += f"✅ {step_name.replace('_', ' ').title()}\n"
                if isinstance(step_result, dict):
                    for key, value in step_result.items():
                        results_text += f"   • {key}: {value}\n"
                results_text += "\n"
        
        # Add data summary
        if self.analysis_adata is not None:
            results_text += f"📈 Final Dataset:\n"
            results_text += f"• Cells: {self.analysis_adata.n_obs:,}\n"
            results_text += f"• Genes: {self.analysis_adata.n_vars:,}\n"
            
            if 'leiden' in self.analysis_adata.obs.columns:
                n_clusters = len(set(self.analysis_adata.obs['leiden']))
                results_text += f"• Clusters: {n_clusters}\n"
            
            results_text += "\n"
        
        self.results_text.setText(results_text)
        
        # Update data table with sample of results
        self.update_data_table()
    
    def update_data_table(self):
        """Update the data table with analysis results"""
        if self.analysis_adata is None:
            return
        
        # Show first 100 cells and their metadata
        obs_df = self.analysis_adata.obs.head(100)
        
        self.data_table.setRowCount(len(obs_df))
        self.data_table.setColumnCount(len(obs_df.columns))
        self.data_table.setHorizontalHeaderLabels(obs_df.columns.tolist())
        
        for i, (idx, row) in enumerate(obs_df.iterrows()):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.data_table.setItem(i, j, item)
        
        self.data_table.resizeColumnsToContents()
    
    def create_visualizations(self):
        """Create visualization plots after analysis completion"""
        if not VISUALIZATION_AVAILABLE or self.analysis_adata is None:
            return
        
        try:
            # Remove placeholder
            if hasattr(self, 'viz_placeholder') and self.viz_placeholder is not None:
                self.viz_layout.removeWidget(self.viz_placeholder)
                self.viz_placeholder.deleteLater()
                self.viz_placeholder = None
            
            # Create matplotlib plotter widget with output directory
            self.viz_widget = MatplotlibPlotter(
                self.analysis_adata, 
                self, 
                output_dir=str(self.output_dir)
            )
            self.viz_layout.addWidget(self.viz_widget)
            
            logger.info("Visualization plots created successfully")
            logger.info(f"Plots will be saved to: {self.output_dir / 'plots'}")
            
        except Exception as e:
            logger.error(f"Failed to create visualizations: {e}")
            
            # Show error message in viz tab
            error_label = QLabel(f"❌ Failed to create visualizations:\n{str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #d32f2f; font-size: 12px; padding: 20px;")
            self.viz_layout.addWidget(error_label)
    
    def export_results(self):
        """Show export results dialog"""
        if self.analysis_adata is None:
            QMessageBox.information(
                self,
                "No Results",
                "No analysis results to export. Please run analysis first."
            )
            return
        
        # Show what has been automatically saved
        export_info = f"📁 Results have been automatically saved to:\n\n"
        export_info += f"📂 {self.output_dir.absolute()}\n\n"
        
        # List what's been saved
        export_info += "📋 Saved Files:\n\n"
        
        # Check intermediate data
        intermediate_dir = self.output_dir / "intermediate_data"
        if intermediate_dir.exists():
            export_info += "🔬 Key Analysis Checkpoints:\n"
            for h5ad_file in intermediate_dir.glob("*.h5ad"):
                export_info += f"   • {h5ad_file.name}\n"
            export_info += "\n"
        
        # Check metadata
        metadata_dir = self.output_dir / "metadata"
        if metadata_dir.exists():
            csv_files = list(metadata_dir.glob("*.csv"))
            if csv_files:
                export_info += f"📊 Metadata Files ({len(csv_files)} files):\n"
                for csv_file in sorted(csv_files)[:5]:  # Show first 5
                    export_info += f"   • {csv_file.name}\n"
                if len(csv_files) > 5:
                    export_info += f"   • ... and {len(csv_files) - 5} more\n"
                export_info += "\n"
        
        # Check plots
        plots_dir = self.output_dir / "plots"
        if plots_dir.exists():
            plot_files = sorted(
                list(plots_dir.glob("*.png")) +
                list(plots_dir.glob("*.pdf")) +
                list(plots_dir.glob("*.svg"))
            )
            if plot_files:
                export_info += f"📈 Visualization Plots ({len(plot_files)} files: PNG/PDF/SVG):\n"
                for plot_file in sorted(plot_files)[:5]:  # Show first 5
                    export_info += f"   • {plot_file.name}\n"
                if len(plot_files) > 5:
                    export_info += f"   • ... and {len(plot_files) - 5} more\n"
                export_info += "\n"
        
        # Check logs
        logs_dir = self.output_dir / "logs"
        if logs_dir.exists():
            export_info += "📝 Execution Logs:\n"
            for log_file in logs_dir.glob("*.txt"):
                export_info += f"   • {log_file.name}\n"
            export_info += "\n"
        
        export_info += "✨ All results are automatically saved during analysis!\n"
        export_info += "You can find intermediate data, metadata, plots, and logs in the results folder."
        
        # Create custom dialog
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Export Results")
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setText("📤 Export Results Summary")
        dialog.setDetailedText(export_info)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Add button to open results folder
        open_folder_btn = dialog.addButton("📁 Open Results Folder", QMessageBox.ButtonRole.ActionRole)
        
        result = dialog.exec()
        
        # Handle button clicks
        if dialog.clickedButton() == open_folder_btn:
            self.open_results_folder()
    
    def open_results_folder(self):
        """Open the results folder in file manager"""
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(self.output_dir)], check=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(self.output_dir)], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(self.output_dir)], check=True)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Cannot Open Folder",
                f"Could not open results folder automatically.\n\n"
                f"Please navigate to: {self.output_dir.absolute()}\n\n"
                f"Error: {e}"
            ) 