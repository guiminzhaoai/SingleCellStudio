# Getting Started with SingleCellStudio

Welcome to SingleCellStudio development! This guide will help you set up the development environment and start contributing to the project.

## 🚀 Quick Start

### For Users (When Released)
```bash
# Download installer from website
# Run SingleCellStudio-Setup.exe
# Follow installation wizard

# Or via pip (future release)
pip install singlecellstudio
singlecellstudio --gui
```

### For Developers

#### 1. Prerequisites
- **Python 3.8+** (Python 3.10 recommended)
- **Git** for version control
- **Windows 10/11** (primary target platform)
- **16GB+ RAM** (32GB recommended for large datasets)

#### 2. Clone Repository
```bash
git clone https://github.com/yourcompany/SingleCellStudio.git
cd SingleCellStudio
```

#### 3. Create Virtual Environment
```bash
# Using venv (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Or using conda
conda create -n singlecellstudio python=3.10
conda activate singlecellstudio
```

#### 4. Install Dependencies
```bash
# Development dependencies (includes all packages)
pip install -r requirements-dev.txt

# Or just runtime dependencies
pip install -r requirements.txt
```

#### 5. Verify Installation
```bash
# Check system requirements
python src/main.py --check

# Run basic GUI demo
python prototype/basic_gui_demo.py

# Run main application (shows placeholder message)
python src/main.py --gui
```

## 🛠️ Development Setup

### IDE Configuration

#### Visual Studio Code (Recommended)
1. Install Python extension
2. Install PySide6 extension
3. Configure settings:
```json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true
}
```

#### PyCharm
1. Set Python interpreter to virtual environment
2. Enable PySide6 support
3. Configure code style to use Black formatter

### Code Quality Tools

#### Linting and Formatting
```bash
# Format code with Black
black src/ tests/ prototype/

# Sort imports
isort src/ tests/ prototype/

# Lint with flake8
flake8 src/ tests/ prototype/

# Type checking with mypy
mypy src/
```

#### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Testing

#### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src/

# GUI tests (requires display)
pytest tests/gui/

# Specific test file
pytest tests/test_analysis.py
```

#### Write Tests
```python
# Example test file: tests/test_example.py
import pytest
from src.analysis.engine import AnalysisEngine

def test_analysis_engine_creation():
    engine = AnalysisEngine()
    assert engine is not None

def test_data_loading():
    # Test data loading functionality
    pass
```

## 📁 Project Structure Overview

```
SingleCellStudio/
├── src/                    # Main source code
│   ├── gui/               # User interface (PySide6)
│   ├── analysis/          # Analysis algorithms
│   ├── visualization/     # Plotting and charts
│   ├── data/             # Data management
│   ├── utils/            # Utility functions
│   ├── main.py           # Application entry point
│   └── version.py        # Version information
├── prototype/             # Early prototypes and demos
├── tests/                # Unit and integration tests
├── docs/                 # Documentation
├── resources/            # Icons, themes, sample data
├── examples/             # Example workflows
└── scripts/             # Build and deployment scripts
```

## 🎯 Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/new-analysis-method

# Make changes
# ... edit files ...

# Run tests
pytest

# Format code
black src/

# Commit changes
git add .
git commit -m "Add new analysis method"

# Push and create PR
git push origin feature/new-analysis-method
```

### 2. GUI Development
```bash
# Run GUI prototype
python prototype/basic_gui_demo.py

# Edit GUI components
# ... modify src/gui/ files ...

# Test GUI changes
python src/main.py --gui --debug
```

### 3. Analysis Development
```bash
# Create new analysis module
touch src/analysis/new_method.py

# Implement algorithm
# ... add analysis code ...

# Add tests
touch tests/test_new_method.py

# Test implementation
pytest tests/test_new_method.py
```

## 🧪 Testing Your Changes

### Manual Testing
```bash
# Test basic functionality
python src/main.py --check
python src/main.py --version

# Test GUI (shows placeholder for now)
python src/main.py --gui

# Test prototype demo
python prototype/basic_gui_demo.py
```

### Automated Testing
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# GUI tests (when implemented)
pytest tests/gui/

# Performance tests
pytest tests/performance/
```

## 📚 Key Development Areas

### 1. GUI Development (PySide6)
- **Location**: `src/gui/`
- **Key Files**: `main_window.py`, `analysis_panel.py`
- **Skills Needed**: PySide6, UI/UX design
- **Getting Started**: Study `prototype/basic_gui_demo.py`

### 2. Analysis Engine
- **Location**: `src/analysis/`
- **Key Files**: `engine.py`, `quality_control.py`
- **Skills Needed**: scanpy, pandas, numpy
- **Getting Started**: Implement basic QC functions

### 3. Visualization
- **Location**: `src/visualization/`
- **Key Files**: `plots.py`, `interactive.py`
- **Skills Needed**: matplotlib, plotly, pyqtgraph
- **Getting Started**: Create basic scatter plots

### 4. Data Management
- **Location**: `src/data/`
- **Key Files**: `manager.py`, `loaders.py`
- **Skills Needed**: h5py, pandas, anndata
- **Getting Started**: Implement 10X data loading

## 🐛 Debugging

### Common Issues

#### 1. PySide6 Import Errors
```bash
# Install PySide6
pip install PySide6

# On Linux, may need additional packages
sudo apt-get install python3-pyside6
```

#### 2. Matplotlib Backend Issues
```python
# In your code, set backend explicitly
import matplotlib
matplotlib.use('Qt5Agg')
```

#### 3. Memory Issues with Large Datasets
```python
# Use chunked processing
import dask
# Process data in chunks
```

### Debug Mode
```bash
# Run with debug logging
python src/main.py --debug

# Check log files
tail -f singlecellstudio.log
```

## 📖 Learning Resources

### Single Cell Analysis
- [scanpy tutorials](https://scanpy.readthedocs.io/en/stable/tutorials.html)
- [Single Cell Best Practices](https://www.sc-best-practices.org/)
- [Seurat tutorials](https://satijalab.org/seurat/articles/get_started.html)

### PySide6 Development
- [PySide6 Documentation](https://www.riverbankcomputing.com/static/Docs/PySide6/)
- [Qt for Python](https://doc.qt.io/qtforpython/)
- [PySide6 Tutorial](https://realpython.com/python-pyside6-gui-calculator/)

### Scientific Python
- [NumPy User Guide](https://numpy.org/doc/stable/user/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Tutorials](https://matplotlib.org/stable/tutorials/index.html)

## 🤝 Contributing

### Code Style
- Follow PEP 8 style guide
- Use Black for code formatting
- Add type hints where possible
- Write docstrings for all functions

### Commit Messages
```
feat: add new clustering algorithm
fix: resolve memory leak in data loading
docs: update installation instructions
test: add unit tests for QC module
```

### Pull Request Process
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Update documentation
5. Submit pull request
6. Address review feedback

## 🆘 Getting Help

### Documentation
- [API Reference](docs/api-reference.md)
- [User Manual](docs/user-manual.md)
- [Architecture Guide](docs/architecture.md)

### Community
- [GitHub Issues](https://github.com/singlecellstudio/issues)
- [Discussion Forum](https://github.com/singlecellstudio/discussions)
- [Developer Chat](https://discord.gg/singlecellstudio)

### Support
- **Email**: dev-support@singlecellstudio.com
- **Documentation**: https://docs.singlecellstudio.com
- **Bug Reports**: https://github.com/singlecellstudio/issues

---

**Ready to start developing?** Begin with the [basic GUI demo](prototype/basic_gui_demo.py) to see the interface in action, then explore the codebase and start contributing! 