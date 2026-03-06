# GitHub Setup Guide for SingleCellStudio

This guide will walk you through uploading your SingleCellStudio project to GitHub.

## 🚀 Quick Setup (Recommended)

### Step 1: Initialize Git Repository
```bash
cd SingleCellStudio

# Initialize git repository
git init

# Add all files to staging
git add .

# Create initial commit
git commit -m "🎉 Initial release: SingleCellStudio v0.1.0-dev

✅ Complete project foundation established
✅ PySide6 GUI framework operational  
✅ Cross-platform compatibility (Linux/Windows/macOS)
✅ Interactive demo working
✅ Professional development environment

Features:
- Main application with GUI
- Interactive prototype demo
- Comprehensive documentation
- Testing framework
- Commercial licensing
- 25+ scientific dependencies integrated

Milestone 1 Complete: Ready for core development phase"
```

### Step 2: Create GitHub Repository
1. **Go to GitHub**: https://github.com
2. **Sign in** to your account (or create one if needed)
3. **Click "New Repository"** (green button or + icon)
4. **Repository Settings**:
   - **Repository name**: `SingleCellStudio`
   - **Description**: `Commercial Single Cell Transcriptome Analysis Software - Professional platform for single cell RNA-seq analysis`
   - **Visibility**: 
     - ✅ **Private** (recommended for commercial project)
     - ⚠️ Public (only if you want open source)
   - **Initialize**: ❌ Don't check any boxes (we already have files)
5. **Click "Create repository"**

### Step 3: Connect Local Repository to GitHub
```bash
# Remove the old remote
git remote remove origin

# Add the correct remote
git remote add origin https://github.com/BioinfoKangaroo/SingleCellStudio.git

# Verify it's correct
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

## 📋 Detailed Setup Instructions

### Prerequisites
- **Git installed**: `git --version` (install from https://git-scm.com if needed)
- **GitHub account**: Create at https://github.com if needed
- **Command line access**: Terminal/PowerShell/WSL

### Alternative: GitHub Desktop (GUI Method)
1. **Download GitHub Desktop**: https://desktop.github.com
2. **Install and sign in** to your GitHub account
3. **Add local repository**:
   - File → Add Local Repository
   - Choose your `SingleCellStudio` folder
   - Click "create a repository"
4. **Publish to GitHub**:
   - Click "Publish repository"
   - Set name: `SingleCellStudio`
   - Choose Private/Public
   - Click "Publish repository"

## 🔧 Repository Configuration

### 1. Add Repository Secrets (for CI/CD later)
Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets for future use:
- `PYPI_TOKEN` (for package publishing)
- `CODECOV_TOKEN` (for code coverage)
- `DOCKER_USERNAME` / `DOCKER_PASSWORD` (for containerization)

### 2. Set Up Branch Protection
Repository → Settings → Branches → Add rule:
- **Branch name pattern**: `main`
- **Require pull request reviews**: ✅
- **Require status checks**: ✅
- **Restrict pushes**: ✅

### 3. Configure Issues and Projects
- **Enable Issues**: For bug tracking and feature requests
- **Create Project Board**: For development planning
- **Add Issue Templates**: For standardized bug reports

## 📝 Recommended Repository Structure

Your repository should look like this on GitHub:
```
SingleCellStudio/
├── 📄 README.md                 # Project overview and features
├── 📄 PROJECT_PLAN.md          # 3-year development roadmap  
├── 📄 DEVELOPMENT_LOG.md       # Development milestones and progress
├── 📄 GETTING_STARTED.md       # Setup and development guide
├── 📄 GITHUB_SETUP.md          # This file
├── 📄 LICENSE                  # Commercial license
├── 📄 .gitignore              # Git ignore patterns
├── 📄 setup.py                # Package configuration
├── 📄 requirements.txt        # Production dependencies
├── 📄 requirements-dev.txt    # Development dependencies
├── 📄 pytest.ini             # Testing configuration
├── 📁 src/                    # Source code
├── 📁 tests/                  # Test suite
├── 📁 docs/                   # Documentation
├── 📁 prototype/              # Prototypes and demos
├── 📁 examples/               # Example workflows
├── 📁 resources/              # Icons, themes, data
└── 📁 scripts/               # Build and deployment scripts
```

## 🏷️ Tagging Releases

### Create Your Latest Release (v0.2.0-alpha)
```bash
# Tag the current milestone - Data Loading Complete
git tag -a v0.2.0-alpha -m "Milestone 2: Core Data Loading System Complete

✅ Multi-format data loading (10X MTX, 10X H5, H5AD, CSV/TSV)
✅ Professional data import dialog with validation
✅ Smart file/folder selection interface
✅ Real-time data preview and quality control
✅ Background loading with progress tracking
✅ Comprehensive error handling and recovery

This alpha release provides production-ready data import 
capabilities rivaling commercial single cell analysis platforms."

# Push tags to GitHub
git push origin --tags
```

### Previous Release (v0.1.0-alpha) - Foundation
```bash
# If you need to tag the foundation milestone separately
git tag -a v0.1.0-alpha -m "Milestone 1: Foundation & GUI Framework Complete

✅ Project foundation established
✅ PySide6 GUI framework operational
✅ Cross-platform compatibility verified
✅ Interactive demo working
✅ Development environment ready"

# Push tags to GitHub
git push origin --tags
```

### Create GitHub Release (v0.2.0-alpha)
1. Go to your repository on GitHub
2. Click **"Releases"** → **"Create a new release"**
3. **Choose tag**: `v0.2.0-alpha`
4. **Release title**: `SingleCellStudio v0.2.0-alpha - Data Loading System Complete`
5. **Description**:
```markdown
## 🎉 Milestone 2: Core Data Loading System Complete

This alpha release provides **production-ready data import capabilities** that rival commercial single cell analysis platforms. SingleCellStudio now supports all major scRNA-seq data formats with professional-grade validation and user experience.

### ✅ Major Achievements
- **Multi-Format Data Loading**: 10X MTX folders, 10X H5 files, AnnData H5AD, CSV/TSV
- **Professional Import Dialog**: 3-tab interface with file/folder selection, preview, and validation
- **Smart Auto-Detection**: Automatic format identification and validation
- **Real-Time Preview**: Data dimensions, sample content, and quality metrics
- **Background Loading**: Non-blocking import with progress tracking
- **Comprehensive Validation**: Quality control with warnings and recommendations

### 🚀 What's Working Now
- **Data Import**: Load any common scRNA-seq format with professional interface
- **Quality Control**: Automatic validation with sparsity, cell/gene counts, and format compliance
- **Error Recovery**: Graceful handling of loading failures with helpful guidance
- **Cross-Platform**: Tested on Linux/WSL, optimized for Windows
- **Performance**: Efficient loading for datasets up to 100K+ cells

### 🎯 Data Formats Supported
| Format | Support | Features |
|--------|---------|----------|
| **10X MTX** | ✅ Complete | Folder auto-detection, legacy support |
| **10X H5** | ✅ Complete | Genome selection, metadata preservation |
| **H5AD** | ✅ Complete | Full AnnData compatibility |
| **CSV/TSV** | ✅ Complete | Auto-delimiter, compression support |

### 📦 Installation & Usage
```bash
git clone https://github.com/YOUR_USERNAME/SingleCellStudio.git
cd SingleCellStudio
pip install -r requirements-dev.txt

# Launch main application
python src/main.py --gui

# Click "Import Data" to test with your scRNA-seq files
```

### 🧪 Test Data Loading
```bash
# Command-line testing
python examples/test_data_loading.py /path/to/your/data

# Try with sample data (if available)
python examples/test_data_loading.py examples/sample_data/filtered_feature_bc_matrix
```

### 🎯 Next Development Phase
- **Analysis Pipeline**: Quality control algorithms and normalization methods
- **Visualization Engine**: Interactive UMAP, t-SNE, and expression plots
- **Clustering Tools**: Leiden and Louvain algorithms with parameter tuning

This release marks SingleCellStudio as **ready for real scientific data analysis** with professional-grade data handling capabilities.
```

6. **Check "This is a pre-release"** (since it's alpha)
7. **Click "Publish release"**

## 🔄 Ongoing Development Workflow

### Daily Development
```bash
# Start development
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/data-import

# Make changes, then commit
git add .
git commit -m "feat: implement 10X Genomics data import

- Add H5 file reader
- Implement data validation
- Create import dialog
- Add progress tracking"

# Push feature branch
git push origin feature/data-import

# Create Pull Request on GitHub
# After review and merge, cleanup
git checkout main
git pull origin main
git branch -d feature/data-import
```

### Commit Message Convention
Use conventional commits for better tracking:
```bash
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug in component"
git commit -m "docs: update documentation"
git commit -m "test: add unit tests"
git commit -m "refactor: improve code structure"
git commit -m "perf: optimize performance"
git commit -m "style: format code"
```

## 🤝 Collaboration Setup

### For Team Development
1. **Add Collaborators**: Repository → Settings → Manage access
2. **Create Teams**: If using GitHub organization
3. **Set Up Code Review**: Require PR reviews before merging
4. **Use Project Boards**: For task management and sprint planning

### Issue Templates
Create `.github/ISSUE_TEMPLATE/` with:
- `bug_report.md` - For bug reports
- `feature_request.md` - For new features
- `question.md` - For questions and support

## 📊 Repository Analytics

### Enable Insights
- **Traffic**: Monitor repository visits
- **Commits**: Track development activity
- **Code frequency**: Analyze development patterns
- **Contributors**: See team contributions

### Badges for README
Add status badges to your README.md:
```markdown
[![License](https://img.shields.io/badge/license-Commercial-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://www.riverbankcomputing.com/software/pyside6/)
[![Build Status](https://github.com/YOUR_USERNAME/SingleCellStudio/workflows/CI/badge.svg)](https://github.com/YOUR_USERNAME/SingleCellStudio/actions)
```

## 🔒 Security Considerations

### For Commercial Project
- ✅ **Use Private Repository** (recommended)
- ✅ **Secure API keys** in GitHub Secrets
- ✅ **Code scanning** enabled
- ✅ **Dependency alerts** enabled
- ✅ **Branch protection** rules active

### License Considerations
- Your `LICENSE` file specifies commercial use
- Consider adding copyright headers to source files
- Document any third-party licenses used

## 🎯 Success Checklist

After setup, verify:
- [ ] Repository created and code uploaded
- [ ] README.md displays properly
- [ ] All files committed and pushed
- [ ] Release v0.1.0-alpha created
- [ ] Repository settings configured
- [ ] Collaborators added (if applicable)
- [ ] Project board created (optional)
- [ ] Issues enabled for feedback

## 📞 Need Help?

- **Git Documentation**: https://git-scm.com/docs
- **GitHub Guides**: https://guides.github.com
- **GitHub Support**: https://support.github.com

---

**🎉 Congratulations!** Your SingleCellStudio project is now on GitHub and ready for collaborative development! 

# Generate SSH key (press Enter for all prompts)
ssh-keygen -t ed25519 -C "BioinfoKangaroo@gmail.com"

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key to agent
ssh-add ~/.ssh/id_ed25519

# Copy public key to clipboard
cat ~/.ssh/id_ed25519.pub 

## 🔧 **Fix the Remote URL and Authentication**

### Step 1: Update the Remote URL
```bash
cd SingleCellStudio

# Remove the old remote
git remote remove origin

# Add the correct remote
git remote add origin https://github.com/BioinfoKangaroo/SingleCellStudio.git

# Verify it's correct
git remote -v
```

### Step 2: Set Up GitHub Authentication with SSH Keys

1. **Generate SSH Key**:
```bash
# Generate SSH key (press Enter for all prompts)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key to agent
ssh-add ~/.ssh/id_ed25519

# Copy public key to clipboard
cat ~/.ssh/id_ed25519.pub
```

2. **Add SSH Key to GitHub**:
   - Go to GitHub.com → Settings → SSH and GPG keys
   - Click "New SSH key"
   - Title: "SingleCellStudio Development"
   - Paste the public key content
   - Click "Add SSH key"

3. **Update Remote to Use SSH**:
```bash
git remote set-url origin git@github.com:BioinfoKangaroo/SingleCellStudio.git
git push -u origin main
```

## 🚀 **Complete Setup Commands**

Here are the exact commands to run:

```bash
cd SingleCellStudio

# Fix the remote URL (if needed)
git remote remove origin
git remote add origin git@github.com:BioinfoKangaroo/SingleCellStudio.git

# Push to GitHub using SSH
git push -u origin main
```

## 📋 **After Successful Push**

Once the push succeeds, you can:

1. **Create a Release**:
```bash
# Tag the milestone
git tag -a v0.1.0-alpha -m "Milestone 1: Foundation & GUI Framework Complete"
git push origin --tags
```

2. **Verify on GitHub**:
   - Go to https://github.com/BioinfoKangaroo/SingleCellStudio
   - You should see all your files
   - Create a release from the tag

3. **Set Repository to Private** (if desired):
   - Repository → Settings → General → Danger Zone → Change visibility

Would you like me to guide you through creating the Personal Access Token, or do you prefer the SSH key method? 