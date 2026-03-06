"""
SingleCellStudio Matplotlib Backend

PySide6 integration for matplotlib plots in the GUI.
"""

import sys
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt backend for PySide6 compatibility

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QTabWidget, QLabel, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
    QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont

try:
    import anndata as ad
    from .plots import (
        create_umap_plot, create_pca_plot, create_qc_plots,
        create_cluster_plot, create_heatmap, create_violin_plots,
        create_summary_plot
    )
    PLOTS_AVAILABLE = True
except ImportError:
    PLOTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class PlotCanvas(FigureCanvas):
    """Custom matplotlib canvas for PySide6"""
    
    def __init__(self, figure=None, parent=None):
        if figure is None:
            self.figure = Figure(figsize=(8, 6), dpi=100)
        else:
            self.figure = figure
            
        super().__init__(self.figure)
        self.setParent(parent)
        
        # Enable interactive navigation
        self.mpl_connect('button_press_event', self.on_click)
        
    def on_click(self, event):
        """Handle mouse clicks on the plot"""
        if event.dblclick:
            # Reset zoom on double-click
            self.figure.axes[0].autoscale()
            self.draw()

class PlotWidget(QWidget):
    """Widget containing a matplotlib plot with toolbar"""
    
    def __init__(self, figure=None, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout()
        
        # Create canvas
        self.canvas = PlotCanvas(figure, self)
        layout.addWidget(self.canvas)
        
        # Create navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        
        self.setLayout(layout)
    
    def update_figure(self, figure):
        """Update the displayed figure by recreating it as an image"""
        # Clear the current figure
        self.canvas.figure.clear()
        
        try:
            # Simple approach: save figure as image and display it
            import io
            import matplotlib.image as mpimg
            
            # Save the source figure to a buffer
            buf = io.BytesIO()
            figure.savefig(buf, format='png', dpi=100, bbox_inches='tight', 
                          facecolor='white', edgecolor='none')
            buf.seek(0)
            
            # Create new axis and display the image
            ax = self.canvas.figure.add_subplot(111)
            img = mpimg.imread(buf)
            ax.imshow(img)
            ax.axis('off')  # Hide axes for clean display
            
            # Set figure size to match original
            self.canvas.figure.set_size_inches(figure.get_size_inches())
            buf.close()
            
        except Exception as e:
            logger.error(f"Error updating figure: {e}")
            # Fallback: show error message
            ax = self.canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, f'Plot update failed:\n{str(e)}', 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, bbox=dict(boxstyle="round,pad=0.3", 
                   facecolor="lightcoral", alpha=0.7))
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        
        self.canvas.draw()

class PlotGeneratorWorker(QThread):
    """Worker thread for generating plots"""
    
    plot_ready = Signal(object, str)  # figure, plot_type
    plot_failed = Signal(str, str)    # error_message, plot_type
    
    def __init__(self, adata, plot_type, **kwargs):
        super().__init__()
        self.adata = adata
        self.plot_type = plot_type
        self.kwargs = kwargs
    
    def run(self):
        """Generate the requested plot"""
        try:
            if not PLOTS_AVAILABLE:
                raise ImportError("Plotting modules not available")
            
            if self.plot_type == 'umap':
                fig = create_umap_plot(self.adata, **self.kwargs)
            elif self.plot_type == 'pca':
                fig = create_pca_plot(self.adata, **self.kwargs)
            elif self.plot_type == 'qc':
                fig = create_qc_plots(self.adata, **self.kwargs)
            elif self.plot_type == 'clusters':
                fig = create_cluster_plot(self.adata, **self.kwargs)
            elif self.plot_type == 'heatmap':
                fig = create_heatmap(self.adata, **self.kwargs)
            elif self.plot_type in ['violin', 'violin_plots']:
                fig = create_violin_plots(self.adata, **self.kwargs)
            elif self.plot_type == 'summary':
                fig = create_summary_plot(self.adata, **self.kwargs)
            else:
                raise ValueError(f"Unknown plot type: {self.plot_type}")
            
            self.plot_ready.emit(fig, self.plot_type)
            
        except Exception as e:
            self.plot_failed.emit(str(e), self.plot_type)

class MatplotlibPlotter(QWidget):
    """Main plotting widget with controls and display area"""
    
    def __init__(self, adata: ad.AnnData, parent=None, output_dir=None):
        super().__init__(parent)
        self.adata = adata
        self.current_plots = {}
        self.workers = {}
        
        # Set up output directory for saving plots
        self.output_dir = self._setup_plots_directory(output_dir)
        
        self.init_ui()
        
        # Generate initial plots
        self.generate_default_plots()
    
    def _setup_plots_directory(self, output_dir=None):
        """
        Set up directory for saving plots
        
        Parameters:
        -----------
        output_dir : str, optional
            Custom output directory path
            
        Returns:
        --------
        Path : Plots output directory path
        """
        if output_dir is None:
            # Create default plots directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plots_dir = Path(f"results/plots_{timestamp}")
        else:
            plots_dir = Path(output_dir) / "plots"
            
        # Create directory
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Plots output directory: {plots_dir.absolute()}")
        return plots_dir
    
    def _save_plot_automatically(self, figure, plot_type, **kwargs):
        """
        Automatically save plot in multiple formats
        
        Parameters:
        -----------
        figure : matplotlib.figure.Figure
            The figure to save
        plot_type : str
            Type of plot for filename
        **kwargs : dict
            Additional parameters for filename
        """
        try:
            # Create filename with timestamp and parameters
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Add relevant parameters to filename
            param_str = ""
            if 'color_by' in kwargs and kwargs['color_by']:
                param_str += f"_colorby_{kwargs['color_by']}"
            if 'cluster_key' in kwargs and kwargs['cluster_key']:
                param_str += f"_clusters_{kwargs['cluster_key']}"
            if 'genes' in kwargs and kwargs['genes']:
                genes_str = "_".join(kwargs['genes'][:3])  # First 3 genes
                param_str += f"_genes_{genes_str}"
                
            base_filename = f"{plot_type}_{timestamp}{param_str}"
            
            # Save in multiple formats
            formats = {
                'png': {'dpi': 300, 'bbox_inches': 'tight', 'facecolor': 'white'},
                'pdf': {'bbox_inches': 'tight', 'facecolor': 'white'},
                'svg': {'bbox_inches': 'tight', 'facecolor': 'white'}
            }
            
            saved_files = []
            for fmt, save_kwargs in formats.items():
                try:
                    output_file = self.output_dir / f"{base_filename}.{fmt}"
                    figure.savefig(output_file, format=fmt, **save_kwargs)
                    saved_files.append(output_file)
                except Exception as e:
                    logger.warning(f"Failed to save {fmt} format: {e}")
            
            if saved_files:
                logger.info(f"Plot saved: {len(saved_files)} formats - {base_filename}")
                return saved_files
            else:
                logger.warning(f"No plot formats saved for {plot_type}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to save plot automatically: {e}")
            return []
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Plot controls
        controls_group = QGroupBox("Plot Controls")
        controls_layout = QGridLayout()
        
        # Plot type selector
        controls_layout.addWidget(QLabel("Plot Type:"), 0, 0)
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems([
            "UMAP", "PCA", "QC Plots", "Clusters", 
            "Summary", "Heatmap", "Violin Plots"
        ])
        self.plot_type_combo.currentTextChanged.connect(self.on_plot_type_changed)
        controls_layout.addWidget(self.plot_type_combo, 0, 1)
        
        # Color by selector
        controls_layout.addWidget(QLabel("Color by:"), 0, 2)
        self.color_by_combo = QComboBox()
        self.update_color_options()
        controls_layout.addWidget(self.color_by_combo, 0, 3)
        
        # Generate plot button
        self.generate_btn = QPushButton("Generate Plot")
        self.generate_btn.clicked.connect(self.generate_current_plot)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        controls_layout.addWidget(self.generate_btn, 0, 4)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Plot display area with tabs
        self.plot_tabs = QTabWidget()
        layout.addWidget(self.plot_tabs)
        
        self.setLayout(layout)
    
    def update_color_options(self):
        """Update color by options based on available data"""
        self.color_by_combo.clear()
        
        # Add categorical columns
        categorical_cols = []
        for col in self.adata.obs.columns:
            if self.adata.obs[col].dtype == 'category' or self.adata.obs[col].dtype == 'object':
                categorical_cols.append(col)
        
        # Add numerical columns
        numerical_cols = []
        for col in self.adata.obs.columns:
            if self.adata.obs[col].dtype in ['int64', 'float64']:
                numerical_cols.append(col)
        
        # Populate combo box
        if 'leiden' in categorical_cols:
            self.color_by_combo.addItem('leiden')
        
        for col in sorted(categorical_cols):
            if col != 'leiden':
                self.color_by_combo.addItem(col)
        
        if numerical_cols:
            self.color_by_combo.addItem("---")
            for col in sorted(numerical_cols):
                self.color_by_combo.addItem(col)
    
    def on_plot_type_changed(self, plot_type):
        """Handle plot type change"""
        # Update available options based on plot type
        if plot_type in ["Heatmap", "Violin Plots"]:
            # These plots need gene selection - could add gene selector here
            pass
    
    def generate_current_plot(self):
        """Generate the currently selected plot"""
        plot_type = self.plot_type_combo.currentText().lower().replace(" ", "_").replace("qc_plots", "qc")
        color_by = self.color_by_combo.currentText()
        
        if color_by == "---" or not color_by:
            color_by = "leiden"  # Default fallback
        
        # Validate that the color_by column exists
        if color_by not in self.adata.obs.columns:
            # Find a suitable alternative
            if 'leiden' in self.adata.obs.columns:
                color_by = 'leiden'
            else:
                # Find first categorical column
                for col in self.adata.obs.columns:
                    if self.adata.obs[col].dtype == 'category' or self.adata.obs[col].dtype == 'object':
                        color_by = col
                        break
                else:
                    color_by = None
        
        kwargs = {}
        
        # Add plot-specific parameters
        if plot_type == "heatmap":
            # For demo, use some common marker genes if they exist
            available_genes = []
            test_genes = ['CD3D', 'CD3E', 'CD8A', 'CD4', 'CD19', 'MS4A1', 'CD14', 'LYZ', 'FCGR3A']
            for gene in test_genes:
                if gene in self.adata.var_names:
                    available_genes.append(gene)
            
            if not available_genes:
                # Use first few genes as fallback
                available_genes = list(self.adata.var_names[:6])
            
            kwargs['genes'] = available_genes[:6]  # Limit to 6 genes
            kwargs['group_by'] = color_by if color_by else 'leiden'
            
        elif plot_type == "violin_plots":
            # Similar logic for violin plots
            available_genes = []
            test_genes = ['CD3D', 'CD8A', 'CD19']
            for gene in test_genes:
                if gene in self.adata.var_names:
                    available_genes.append(gene)
            
            if not available_genes:
                available_genes = list(self.adata.var_names[:3])
            
            kwargs['genes'] = available_genes[:3]
            kwargs['group_by'] = color_by if color_by else 'leiden'
            
        elif plot_type in ['umap', 'pca', 'clusters']:
            if color_by:
                if plot_type == 'clusters':
                    kwargs['cluster_key'] = color_by  # Clusters uses cluster_key, not color_by
                else:
                    kwargs['color_by'] = color_by
        
        # Special handling for plots that don't need color_by
        if plot_type in ['qc', 'summary']:
            pass  # These plots don't use color_by
        
        self.generate_plot(plot_type, **kwargs)
    
    def generate_plot(self, plot_type: str, **kwargs):
        """Generate a specific plot type"""
        # Validate plot requirements
        if plot_type == 'umap' and 'X_umap' not in self.adata.obsm:
            QMessageBox.warning(
                self,
                "UMAP Not Available",
                "UMAP coordinates not found. Please run UMAP analysis first."
            )
            return
        
        if plot_type == 'pca' and 'X_pca' not in self.adata.obsm:
            QMessageBox.warning(
                self,
                "PCA Not Available", 
                "PCA coordinates not found. Please run PCA analysis first."
            )
            return
        
        if plot_type in ['heatmap', 'violin_plots'] and 'genes' not in kwargs:
            QMessageBox.warning(
                self,
                "No Genes Available",
                f"No suitable genes found for {plot_type}."
            )
            return
        
        # Stop existing worker if any
        if plot_type in self.workers and self.workers[plot_type].isRunning():
            self.workers[plot_type].quit()
            self.workers[plot_type].wait()
        
        # Store kwargs for saving later
        self.plot_kwargs = kwargs.copy()
        
        # Start new worker
        worker = PlotGeneratorWorker(self.adata, plot_type, **kwargs)
        worker.plot_ready.connect(self.on_plot_ready)
        worker.plot_failed.connect(self.on_plot_failed)
        
        self.workers[plot_type] = worker
        worker.start()
        
        # Update button state
        self.generate_btn.setText("Generating...")
        self.generate_btn.setEnabled(False)
        
        logger.info(f"Started generating {plot_type} plot with kwargs: {kwargs}")
    
    def on_plot_ready(self, figure, plot_type):
        """Handle completed plot generation"""
        try:
            # Automatically save the plot
            saved_files = self._save_plot_automatically(
                figure, plot_type, **getattr(self, 'plot_kwargs', {})
            )
            
            # Create or update plot widget
            if plot_type in self.current_plots:
                # Update existing plot
                self.current_plots[plot_type].update_figure(figure)
            else:
                # Create new plot widget
                plot_widget = PlotWidget(figure, self)
                self.current_plots[plot_type] = plot_widget
                
                # Add to tabs
                tab_name = plot_type.replace('_', ' ').title()
                self.plot_tabs.addTab(plot_widget, tab_name)
            
            # Switch to the generated plot tab
            tab_name = plot_type.replace('_', ' ').title()
            for i in range(self.plot_tabs.count()):
                if self.plot_tabs.tabText(i) == tab_name:
                    self.plot_tabs.setCurrentIndex(i)
                    break
            
            # Log success with save information
            if saved_files:
                logger.info(f"Generated and saved {plot_type} plot: {len(saved_files)} formats")
            else:
                logger.info(f"Generated {plot_type} plot successfully")
            
        except Exception as e:
            logger.error(f"Error handling completed plot: {e}")
            self.on_plot_failed(str(e), plot_type)
            return
        
        # Reset button
        self.generate_btn.setText("Generate Plot")
        self.generate_btn.setEnabled(True)
    
    def on_plot_failed(self, error_message, plot_type):
        """Handle failed plot generation"""
        QMessageBox.warning(
            self,
            "Plot Generation Failed",
            f"Failed to generate {plot_type} plot:\n{error_message}"
        )
        
        # Reset button
        self.generate_btn.setText("Generate Plot")
        self.generate_btn.setEnabled(True)
        
        logger.error(f"Failed to generate {plot_type} plot: {error_message}")
    
    def generate_default_plots(self):
        """Generate default plots after analysis"""
        # Generate essential plots with delays to avoid threading issues
        default_plots = ['summary', 'umap', 'qc']
        
        for i, plot_type in enumerate(default_plots):
            if plot_type == 'umap' and 'X_umap' not in self.adata.obsm:
                continue
            if plot_type == 'qc' and 'n_genes_by_counts' not in self.adata.obs:
                continue
                
            kwargs = {}
            if plot_type == 'umap' and 'leiden' in self.adata.obs:
                kwargs['color_by'] = 'leiden'
            
            # Use QTimer to stagger plot generation
            QTimer.singleShot(i * 500, lambda pt=plot_type, kw=kwargs: self.generate_plot(pt, **kw))
    
    def clear_plots(self):
        """Clear all plots"""
        self.plot_tabs.clear()
        self.current_plots.clear()
        
        # Stop all workers
        for worker in self.workers.values():
            worker.quit()
            worker.wait()
        self.workers.clear()
    
    def export_plot(self, plot_type: str, file_path: str):
        """Export a specific plot to file and ensure PDF export is available."""
        if plot_type in self.current_plots:
            figure = self.current_plots[plot_type].canvas.figure
            output_path = Path(file_path)

            # Save user-requested format first
            save_kwargs = {'bbox_inches': 'tight'}
            if output_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.tif']:
                save_kwargs['dpi'] = 300
            figure.savefig(output_path, **save_kwargs)

            # Always provide a PDF export companion for publication workflows
            pdf_path = output_path.with_suffix('.pdf')
            if pdf_path != output_path:
                figure.savefig(pdf_path, bbox_inches='tight')

            return True
        return False
