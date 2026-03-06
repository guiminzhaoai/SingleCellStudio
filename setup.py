#!/usr/bin/env python3
"""
SingleCellStudio - Commercial Single Cell Transcriptome Analysis Software
Setup script for packaging and distribution
"""

from setuptools import setup, find_packages
import os
import sys

# Ensure Python 3.8+
if sys.version_info < (3, 8):
    raise RuntimeError("SingleCellStudio requires Python 3.8 or higher")

# Read version from version file
def get_version():
    """Get version from version.py file"""
    version_file = os.path.join(os.path.dirname(__file__), 'src', 'version.py')
    if os.path.exists(version_file):
        with open(version_file) as f:
            exec(f.read())
            return locals()['__version__']
    return "0.1.0"

# Read long description from README
def get_long_description():
    """Get long description from README.md"""
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, encoding='utf-8') as f:
            return f.read()
    return ""

# Read requirements from requirements.txt
def get_requirements():
    """Get requirements from requirements.txt"""
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_file):
        with open(requirements_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    requirements.append(line)
    return requirements

setup(
    # Basic package information
    name="singlecellstudio",
    version=get_version(),
    description="Commercial Single Cell Transcriptome Analysis Software",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    
    # Author and contact information
    author="SingleCellStudio Inc.",
    author_email="info@singlecellstudio.com",
    url="https://www.singlecellstudio.com",
    
    # License and classification
    license="Commercial",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
        "Environment :: Win32 (MS Windows)",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    
    # Package structure
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    
    # Dependencies
    python_requires=">=3.8",
    install_requires=get_requirements(),
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.1.0",
            "pytest-qt>=4.1.0",
            "pytest-cov>=3.0.0",
            "black>=22.6.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=0.971",
        ],
        "gpu": [
            "cupy-cuda11x>=11.0.0",
            "rapids-singlecell>=0.8.0",
        ],
        "docs": [
            "sphinx>=5.1.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.19.0",
        ],
    },
    
    # Entry points for command-line tools
    entry_points={
        "console_scripts": [
            "singlecellstudio=main:main",
            "scs=main:main",
        ],
        "gui_scripts": [
            "singlecellstudio-gui=main:main_gui",
            "scs-gui=main:main_gui",
        ],
    },
    
    # Package data
    package_data={
        "singlecellstudio": [
            "resources/*.png",
            "resources/*.ico",
            "resources/*.qss",
            "resources/themes/*.json",
            "resources/icons/*.png",
            "resources/icons/*.svg",
        ],
    },
    
    # Additional metadata
    keywords="single-cell transcriptomics bioinformatics genomics RNA-seq analysis visualization",
    project_urls={
        "Homepage": "https://www.singlecellstudio.com",
        "Documentation": "https://docs.singlecellstudio.com",
        "Source": "https://github.com/singlecellstudio/singlecellstudio",
        "Bug Reports": "https://github.com/singlecellstudio/singlecellstudio/issues",
        "Funding": "https://www.singlecellstudio.com/funding",
    },
    
    # Zip safety
    zip_safe=False,
) 