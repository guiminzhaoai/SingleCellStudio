"""
Data Import Dialog for SingleCellStudio

This module provides a GUI dialog for importing single cell RNA-seq data
using the data loading functionality.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import numpy as np

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QFileDialog, QProgressBar, QCheckBox, QGroupBox,
    QMessageBox, QTabWidget, QWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon

# Import our data modules
try:
    from ..data import DataLoader, DataFormat, get_data_info, auto_detect_format
    from ..data.validators import DataValidator
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data import DataLoader, DataFormat, get_data_info, auto_detect_format
    from data.validators import DataValidator

logger = logging.getLogger(__name__)

class DataLoadingThread(QThread):
    """Thread for loading data in the background"""
    
    progress_updated = Signal(int)
    status_updated = Signal(str)
    data_loaded = Signal(object)  # AnnData object
    error_occurred = Signal(str)
    
    def __init__(self, file_path: str, format_type: Optional[DataFormat] = None):
        super().__init__()
        self.file_path = file_path
        self.format_type = format_type
        self.loader = DataLoader()
    
    def run(self):
        """Run the data loading in background"""
        try:
            self.status_updated.emit("Detecting format...")
            self.progress_updated.emit(10)
            
            # Auto-detect format if not specified
            if self.format_type is None:
                self.format_type = auto_detect_format(self.file_path)
            
            self.status_updated.emit(f"Loading {self.format_type.value} data...")
            self.progress_updated.emit(30)
            
            # Load the data
            adata = self.loader.load(self.file_path, self.format_type)
            
            self.status_updated.emit("Validating data...")
            self.progress_updated.emit(70)
            
            # Validate the data
            validator = DataValidator()
            validation_results = validator.validate_adata(adata)
            
            # Add validation results to metadata
            adata.uns['scs_validation'] = validation_results
            
            self.progress_updated.emit(100)
            self.status_updated.emit("Data loaded successfully!")
            
            self.data_loaded.emit(adata)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class DataImportDialog(QDialog):
    """Dialog for importing single cell RNA-seq data"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Single Cell Data - SingleCellStudio")
        self.setModal(True)
        self.resize(800, 600)
        
        self.loaded_data = None
        self.loading_thread = None
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # File selection tab
        self.setup_file_tab()
        
        # Data preview tab
        self.setup_preview_tab()
        
        # Validation tab
        self.setup_validation_tab()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to import data")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.load_button = QPushButton("Load Data")
        self.load_button.setEnabled(False)
        
        self.cancel_button = QPushButton("Cancel")
        self.import_button = QPushButton("Import")
        self.import_button.setEnabled(False)
        
        button_layout.addStretch()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.import_button)
        
        layout.addLayout(button_layout)
    
    def setup_file_tab(self):
        """Set up the file selection tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File selection group
        file_group = QGroupBox("Data File Selection")
        file_layout = QGridLayout(file_group)
        
        # File path
        file_layout.addWidget(QLabel("File/Folder Path:"), 0, 0)
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select a file (.h5, .h5ad, .csv) or folder (10X MTX)")
        file_layout.addWidget(self.file_path_edit, 0, 1)
        
        self.browse_button = QPushButton("Browse... ▼")
        self.browse_button.setToolTip("Click to select file or folder")
        file_layout.addWidget(self.browse_button, 0, 2)
        
        # Format selection
        file_layout.addWidget(QLabel("Data Format:"), 1, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItem("Auto-detect", None)
        self.format_combo.addItem("10X Genomics MTX", DataFormat.TENX_MTX)
        self.format_combo.addItem("10X Genomics H5", DataFormat.TENX_H5)
        self.format_combo.addItem("AnnData H5AD", DataFormat.H5AD)
        self.format_combo.addItem("CSV", DataFormat.CSV)
        self.format_combo.addItem("TSV", DataFormat.TSV)
        file_layout.addWidget(self.format_combo, 1, 1, 1, 2)
        
        layout.addWidget(file_group)
        
        # File info group
        info_group = QGroupBox("File Information")
        info_layout = QGridLayout(info_group)
        
        self.info_labels = {}
        info_fields = [
            ("Format:", "format_label"),
            ("Size:", "size_label"),
            ("Cells:", "cells_label"),
            ("Genes:", "genes_label"),
            ("Status:", "status_label_info")
        ]
        
        for i, (label_text, field_name) in enumerate(info_fields):
            info_layout.addWidget(QLabel(label_text), i, 0)
            label = QLabel("Not detected")
            label.setStyleSheet("color: gray;")
            self.info_labels[field_name] = label
            info_layout.addWidget(label, i, 1)
        
        layout.addWidget(info_group)
        
        # Options group
        options_group = QGroupBox("Loading Options")
        options_layout = QVBoxLayout(options_group)
        
        self.gene_names_combo = QComboBox()
        self.gene_names_combo.addItem("Use gene symbols", "gene_symbols")
        self.gene_names_combo.addItem("Use gene IDs", "gene_ids")
        options_layout.addWidget(QLabel("Gene naming:"))
        options_layout.addWidget(self.gene_names_combo)
        
        self.cache_checkbox = QCheckBox("Cache loaded data")
        options_layout.addWidget(self.cache_checkbox)
        
        layout.addWidget(options_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "File Selection")
    
    def setup_preview_tab(self):
        """Set up the data preview tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Data summary
        summary_group = QGroupBox("Data Summary")
        summary_layout = QGridLayout(summary_group)
        
        self.summary_labels = {}
        summary_fields = [
            ("Cells:", "n_cells"),
            ("Genes:", "n_genes"),
            ("Matrix Type:", "matrix_type"),
            ("Sparsity:", "sparsity"),
            ("Mean Genes/Cell:", "mean_genes_per_cell")
        ]
        
        for i, (label_text, field_name) in enumerate(summary_fields):
            summary_layout.addWidget(QLabel(label_text), i, 0)
            label = QLabel("Not loaded")
            label.setStyleSheet("color: gray;")
            self.summary_labels[field_name] = label
            summary_layout.addWidget(label, i, 1)
        
        layout.addWidget(summary_group)
        
        # Sample data preview
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_table)
        
        layout.addWidget(preview_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Data Preview")
    
    def setup_validation_tab(self):
        """Set up the validation results tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Validation summary
        validation_group = QGroupBox("Validation Summary")
        validation_layout = QGridLayout(validation_group)
        
        self.validation_labels = {}
        validation_fields = [
            ("Status:", "validation_status"),
            ("Errors:", "n_errors"),
            ("Warnings:", "n_warnings"),
            ("Gene ID Format:", "gene_id_format"),
            ("Barcode Format:", "barcode_format")
        ]
        
        for i, (label_text, field_name) in enumerate(validation_fields):
            validation_layout.addWidget(QLabel(label_text), i, 0)
            label = QLabel("Not validated")
            label.setStyleSheet("color: gray;")
            self.validation_labels[field_name] = label
            validation_layout.addWidget(label, i, 1)
        
        layout.addWidget(validation_group)
        
        # Validation details
        details_group = QGroupBox("Validation Details")
        details_layout = QVBoxLayout(details_group)
        
        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setMaximumHeight(200)
        details_layout.addWidget(self.validation_text)
        
        layout.addWidget(details_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Validation")
    
    def setup_connections(self):
        """Set up signal connections"""
        self.browse_button.clicked.connect(self.browse_file)
        self.file_path_edit.textChanged.connect(self.on_file_path_changed)
        self.load_button.clicked.connect(self.load_data)
        self.cancel_button.clicked.connect(self.reject)
        self.import_button.clicked.connect(self.accept)
    
    def browse_file(self):
        """Open file browser to select data file or folder"""
        # Create a menu to choose between file and folder
        from PySide6.QtWidgets import QMenu
        from PySide6.QtCore import QPoint
        
        menu = QMenu(self)
        
        file_action = menu.addAction("📄 Select File (H5, H5AD, CSV, TSV)")
        folder_action = menu.addAction("📁 Select Folder (10X MTX format)")
        
        # Show menu at button position
        button_pos = self.browse_button.mapToGlobal(QPoint(0, self.browse_button.height()))
        action = menu.exec(button_pos)
        
        if action == file_action:
            self._browse_file()
        elif action == folder_action:
            self._browse_folder()
    
    def _browse_file(self):
        """Browse for a single file"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilters([
            "All supported formats (*.h5 *.h5ad *.csv *.tsv)",
            "10X Genomics H5 (*.h5)",
            "AnnData H5AD (*.h5ad)",
            "CSV files (*.csv)",
            "TSV files (*.tsv)",
            "All files (*)"
        ])
        
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            files = file_dialog.selectedFiles()
            if files:
                self.file_path_edit.setText(files[0])
    
    def _browse_folder(self):
        """Browse for a folder (10X MTX format)"""
        folder = QFileDialog.getExistingDirectory(
            self, "Select 10X Genomics MTX folder"
        )
        if folder:
            self.file_path_edit.setText(folder)
    
    def on_file_path_changed(self):
        """Handle file path changes"""
        file_path = self.file_path_edit.text().strip()
        
        if not file_path:
            self.load_button.setEnabled(False)
            self.reset_info_labels()
            return
        
        # Get file info
        try:
            info = get_data_info(file_path)
            self.update_info_labels(info)
            self.load_button.setEnabled(True)
        except Exception as e:
            self.reset_info_labels()
            self.info_labels['status_label_info'].setText(f"Error: {str(e)}")
            self.info_labels['status_label_info'].setStyleSheet("color: red;")
            self.load_button.setEnabled(False)
    
    def update_info_labels(self, info: Dict[str, Any]):
        """Update file information labels"""
        self.info_labels['format_label'].setText(info.get('format', 'Unknown'))
        self.info_labels['format_label'].setStyleSheet("color: black;")
        
        size_mb = info.get('size_mb')
        if size_mb is not None:
            self.info_labels['size_label'].setText(f"{size_mb:.1f} MB")
        else:
            self.info_labels['size_label'].setText("Unknown")
        self.info_labels['size_label'].setStyleSheet("color: black;")
        
        n_cells = info.get('n_cells')
        if n_cells is not None:
            self.info_labels['cells_label'].setText(f"{n_cells:,}")
        else:
            self.info_labels['cells_label'].setText("Unknown")
        self.info_labels['cells_label'].setStyleSheet("color: black;")
        
        n_genes = info.get('n_genes')
        if n_genes is not None:
            self.info_labels['genes_label'].setText(f"{n_genes:,}")
        else:
            self.info_labels['genes_label'].setText("Unknown")
        self.info_labels['genes_label'].setStyleSheet("color: black;")
        
        if info.get('error'):
            self.info_labels['status_label_info'].setText(f"Error: {info['error']}")
            self.info_labels['status_label_info'].setStyleSheet("color: red;")
        else:
            self.info_labels['status_label_info'].setText("Ready to load")
            self.info_labels['status_label_info'].setStyleSheet("color: green;")
    
    def reset_info_labels(self):
        """Reset all info labels"""
        for label in self.info_labels.values():
            label.setText("Not detected")
            label.setStyleSheet("color: gray;")
    
    def load_data(self):
        """Load the selected data file"""
        file_path = self.file_path_edit.text().strip()
        if not file_path:
            return
        
        # Get selected format
        format_type = self.format_combo.currentData()
        
        # Start loading thread
        self.loading_thread = DataLoadingThread(file_path, format_type)
        self.loading_thread.progress_updated.connect(self.progress_bar.setValue)
        self.loading_thread.status_updated.connect(self.status_label.setText)
        self.loading_thread.data_loaded.connect(self.on_data_loaded)
        self.loading_thread.error_occurred.connect(self.on_loading_error)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.load_button.setEnabled(False)
        
        # Start loading
        self.loading_thread.start()
    
    def on_data_loaded(self, adata):
        """Handle successful data loading"""
        self.loaded_data = adata
        
        # Update preview tab
        self.update_data_preview(adata)
        
        # Update validation tab
        self.update_validation_results(adata)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Enable import button
        self.import_button.setEnabled(True)
        self.load_button.setEnabled(True)
        
        # Switch to preview tab
        self.tab_widget.setCurrentIndex(1)
    
    def on_loading_error(self, error_message):
        """Handle loading errors"""
        self.progress_bar.setVisible(False)
        self.load_button.setEnabled(True)
        self.status_label.setText(f"Error: {error_message}")
        
        QMessageBox.critical(
            self, 
            "Data Loading Error", 
            f"Failed to load data:\n\n{error_message}"
        )
    
    def update_data_preview(self, adata):
        """Update the data preview tab"""
        # Update summary labels
        self.summary_labels['n_cells'].setText(f"{adata.n_obs:,}")
        self.summary_labels['n_cells'].setStyleSheet("color: black;")
        
        self.summary_labels['n_genes'].setText(f"{adata.n_vars:,}")
        self.summary_labels['n_genes'].setStyleSheet("color: black;")
        
        matrix_type = "Sparse" if hasattr(adata.X, 'nnz') else "Dense"
        self.summary_labels['matrix_type'].setText(matrix_type)
        self.summary_labels['matrix_type'].setStyleSheet("color: black;")
        
        # Calculate sparsity
        if hasattr(adata.X, 'nnz'):
            sparsity = 1.0 - (adata.X.nnz / (adata.n_obs * adata.n_vars))
            self.summary_labels['sparsity'].setText(f"{sparsity:.1%}")
        else:
            self.summary_labels['sparsity'].setText("N/A")
        self.summary_labels['sparsity'].setStyleSheet("color: black;")
        
        # Mean genes per cell (approximate)
        try:
            from scipy import sparse
            if sparse.issparse(adata.X):
                # For sparse matrices, count non-zero elements per cell
                genes_per_cell = np.array((adata.X > 0).sum(axis=1)).flatten()
            else:
                # For dense matrices, count non-zero elements per cell  
                genes_per_cell = np.sum(adata.X > 0, axis=1)
            mean_genes = float(np.mean(genes_per_cell))
            self.summary_labels['mean_genes_per_cell'].setText(f"{mean_genes:.0f}")
        except Exception:
            self.summary_labels['mean_genes_per_cell'].setText("N/A")
        self.summary_labels['mean_genes_per_cell'].setStyleSheet("color: black;")
        
        # Update preview table (show first few cells and genes)
        n_preview_cells = min(5, adata.n_obs)
        n_preview_genes = min(10, adata.n_vars)
        
        self.preview_table.setRowCount(n_preview_cells)
        self.preview_table.setColumnCount(n_preview_genes)
        
        # Set headers
        self.preview_table.setHorizontalHeaderLabels([
            str(gene)[:20] + "..." if len(str(gene)) > 20 else str(gene)
            for gene in adata.var_names[:n_preview_genes]
        ])
        self.preview_table.setVerticalHeaderLabels([
            str(cell)[:20] + "..." if len(str(cell)) > 20 else str(cell)
            for cell in adata.obs_names[:n_preview_cells]
        ])
        
        # Fill table with data
        for i in range(n_preview_cells):
            for j in range(n_preview_genes):
                # Handle sparse matrices properly
                if hasattr(adata.X, 'toarray'):
                    # For sparse matrices, get the value correctly
                    value = float(adata.X[i, j])
                else:
                    # For dense matrices
                    value = float(adata.X[i, j])
                
                item = QTableWidgetItem(f"{value:.2f}")
                self.preview_table.setItem(i, j, item)
        
        # Resize columns
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    
    def update_validation_results(self, adata):
        """Update the validation results tab"""
        if 'scs_validation' not in adata.uns:
            return
        
        validation = adata.uns['scs_validation']
        
        # Update validation labels
        status = "✅ Passed" if validation['valid'] else "❌ Failed"
        self.validation_labels['validation_status'].setText(status)
        self.validation_labels['validation_status'].setStyleSheet(
            "color: green;" if validation['valid'] else "color: red;"
        )
        
        self.validation_labels['n_errors'].setText(str(len(validation['errors'])))
        self.validation_labels['n_errors'].setStyleSheet("color: black;")
        
        self.validation_labels['n_warnings'].setText(str(len(validation['warnings'])))
        self.validation_labels['n_warnings'].setStyleSheet("color: black;")
        
        info = validation['info']
        self.validation_labels['gene_id_format'].setText(
            info.get('gene_id_format', 'Unknown')
        )
        self.validation_labels['gene_id_format'].setStyleSheet("color: black;")
        
        self.validation_labels['barcode_format'].setText(
            info.get('barcode_format', 'Unknown')
        )
        self.validation_labels['barcode_format'].setStyleSheet("color: black;")
        
        # Update validation text
        text_parts = []
        
        if validation['errors']:
            text_parts.append("❌ ERRORS:")
            for error in validation['errors']:
                text_parts.append(f"  • {error}")
            text_parts.append("")
        
        if validation['warnings']:
            text_parts.append("⚠️ WARNINGS:")
            for warning in validation['warnings']:
                text_parts.append(f"  • {warning}")
            text_parts.append("")
        
        if validation['recommendations']:
            text_parts.append("💡 RECOMMENDATIONS:")
            for rec in validation['recommendations']:
                text_parts.append(f"  • {rec}")
        
        self.validation_text.setPlainText("\n".join(text_parts))
    
    def get_loaded_data(self):
        """Get the loaded data"""
        return self.loaded_data
    
    def get_file_path(self):
        """Get the path of the loaded file"""
        return self.file_path_edit.text().strip() if hasattr(self, 'file_path_edit') else None 