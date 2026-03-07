# SingleCellStudio 模块化开发指南

## 概述

SingleCellStudio 采用模块化架构，允许开发者独立开发分析模块，然后无缝集成到主界面中。这种设计的优势：

- **独立开发**：每个模块可以独立开发和测试
- **动态加载**：模块在运行时自动发现和加载
- **松散耦合**：模块之间通过信号和统一接口通信
- **易于维护**：主窗口代码保持简洁，新功能不会使其变得臃肿

## 架构概览

```
SingleCellStudio/
├── src/
│   └── gui/
│       ├── modular_main_window.py     # 模块化主窗口
│       ├── modules/
│       │   ├── module_registry.py     # 模块注册系统
│       │   ├── example_module.py      # 示例模块
│       │   └── your_module.py         # 你的新模块
│       └── default.qss                # QSS样式文件
```

## 创建新模块

### 步骤1：创建模块文件

在 `src/gui/modules/` 目录下创建一个新的Python文件，文件名必须以 `_module.py` 结尾：

```python
# src/gui/modules/my_analysis_module.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
)
from PySide6.QtCore import Signal
from .module_registry import BaseGUIModule

class MyAnalysisModule(BaseGUIModule):
    """我的自定义分析模块"""
    
    # 定义信号用于与主窗口通信
    analysis_completed = Signal(dict)
    
    @property
    def module_name(self) -> str:
        return "my_analysis"  # 唯一标识符
    
    @property
    def display_name(self) -> str:
        return "我的分析"  # 显示名称
    
    @property
    def description(self) -> str:
        return "自定义单细胞分析模块"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def requirements(self) -> list:
        return ["numpy", "pandas", "scanpy"]  # 依赖包
    
    def create_widget(self, parent=None):
        """创建模块的主界面"""
        widget = QWidget(parent)
        layout = QVBoxLayout()
        
        # 添加你的UI组件
        header = QLabel("我的分析模块")
        layout.addWidget(header)
        
        self.run_btn = QPushButton("运行分析")
        self.run_btn.clicked.connect(self.run_analysis)
        layout.addWidget(self.run_btn)
        
        self.results_text = QTextEdit()
        layout.addWidget(self.results_text)
        
        widget.setLayout(layout)
        self._widget = widget
        return widget
    
    def set_data(self, adata):
        """接收主窗口传来的数据"""
        self.adata = adata
        if adata is not None:
            self.run_btn.setEnabled(True)
    
    def run_analysis(self):
        """执行分析逻辑"""
        if self.adata is None:
            return
        
        # 你的分析代码
        results = {"status": "完成", "cells": self.adata.n_obs}
        
        self.results_text.setText(f"分析完成: {results}")
        
        # 发送信号通知主窗口
        self.analysis_completed.emit(results)
    
    def get_menu_actions(self):
        """返回此模块提供的菜单动作"""
        return [
            {
                "text": "运行我的分析",
                "callback": self.run_analysis,
                "shortcut": "Ctrl+M"
            }
        ]
```

### 步骤2：注册模块（自动）

由于文件名以 `_module.py` 结尾，模块会自动被发现和注册。不需要修改主窗口代码！

### 步骤3：测试模块

运行应用程序：

```bash
python src/gui/modular_main_window.py
```

你的模块将自动出现在界面中。

## 模块开发最佳实践

### 1. 模块结构

```python
class YourModule(BaseGUIModule):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.results = None
    
    # 必须实现的属性
    @property
    def module_name(self) -> str: ...
    @property 
    def display_name(self) -> str: ...
    @property
    def description(self) -> str: ...
    
    # 必须实现的方法
    def create_widget(self, parent=None): ...
    
    # 可选实现的方法
    def initialize(self): ...
    def set_data(self, adata): ...
    def cleanup(self): ...
    def get_menu_actions(self): ...
```

### 2. 信号通信

使用Qt信号与主窗口通信：

```python
from PySide6.QtCore import Signal

class YourModule(BaseGUIModule):
    # 定义信号
    analysis_started = Signal()
    analysis_completed = Signal(dict)
    analysis_failed = Signal(str)
    data_updated = Signal(object)
    
    def some_method(self):
        # 发射信号
        self.analysis_started.emit()
        try:
            # 执行分析
            result = self.do_analysis()
            self.analysis_completed.emit(result)
        except Exception as e:
            self.analysis_failed.emit(str(e))
```

### 3. 错误处理

```python
def create_widget(self, parent=None):
    try:
        # 创建界面
        widget = self._create_ui(parent)
        return widget
    except Exception as e:
        self.logger.error(f"Failed to create widget: {e}")
        # 返回错误显示widget
        return self._create_error_widget(str(e))

def _create_error_widget(self, error_msg):
    widget = QWidget()
    layout = QVBoxLayout()
    error_label = QLabel(f"模块加载失败: {error_msg}")
    layout.addWidget(error_label)
    widget.setLayout(layout)
    return widget
```

### 4. 异步操作

对于长时间运行的分析，使用QThread：

```python
from PySide6.QtCore import QThread, Signal

class AnalysisWorker(QThread):
    finished = Signal(dict)
    progress = Signal(int)
    
    def __init__(self, data):
        super().__init__()
        self.data = data
    
    def run(self):
        # 长时间运行的分析
        for i in range(100):
            # 模拟进度
            self.progress.emit(i)
            time.sleep(0.1)
        
        result = {"status": "完成"}
        self.finished.emit(result)

class YourModule(BaseGUIModule):
    def run_analysis(self):
        self.worker = AnalysisWorker(self.adata)
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.progress.connect(self.update_progress)
        self.worker.start()
```

## 高级功能

### 1. 自定义配置

```python
class YourModule(BaseGUIModule):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = self.load_config()
    
    def load_config(self):
        config_file = Path(__file__).parent / f"{self.module_name}_config.json"
        if config_file.exists():
            import json
            with open(config_file) as f:
                return json.load(f)
        return {}
    
    def save_config(self):
        config_file = Path(__file__).parent / f"{self.module_name}_config.json"
        import json
        with open(config_file, 'w') as f:
            json.dump(self.config, f)
```

### 2. 模块间通信

```python
class YourModule(BaseGUIModule):
    def initialize(self):
        # 获取其他模块的引用
        from .module_registry import registry
        self.other_module = registry.get_module("other_module_name")
    
    def communicate_with_other_module(self):
        if self.other_module:
            # 调用其他模块的方法
            self.other_module.some_method()
```

### 3. 数据验证

```python
def set_data(self, adata):
    """设置数据并验证"""
    if adata is None:
        self.adata = None
        self.disable_controls()
        return
    
    # 验证数据格式
    if not hasattr(adata, 'obs') or not hasattr(adata, 'var'):
        self.logger.error("Invalid data format")
        return
    
    # 检查必需的列
    required_obs = ['n_genes', 'n_counts']
    missing = [col for col in required_obs if col not in adata.obs.columns]
    if missing:
        self.logger.warning(f"Missing required columns: {missing}")
    
    self.adata = adata
    self.enable_controls()
    self.update_ui()
```

## 部署和分发

### 1. 模块打包

创建一个独立的模块包：

```
my_module_package/
├── __init__.py
├── my_module.py
├── requirements.txt
└── README.md
```

### 2. 安装脚本

```python
# install_module.py
import shutil
from pathlib import Path

def install_module(module_file, target_dir):
    """安装模块到SingleCellStudio"""
    target_path = target_dir / "modules" / module_file.name
    shutil.copy2(module_file, target_path)
    print(f"Module installed: {target_path}")

# 使用方法
install_module(Path("my_module.py"), Path("src/gui"))
```

## 示例：完整的差异表达分析模块

```python
# src/gui/modules/differential_expression_module.py

from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, QThread
from .module_registry import BaseGUIModule

class DEAnalysisWorker(QThread):
    finished = Signal(dict)
    progress = Signal(int, str)
    
    def __init__(self, adata, group1, group2):
        super().__init__()
        self.adata = adata
        self.group1 = group1
        self.group2 = group2
    
    def run(self):
        try:
            import scanpy as sc
            
            self.progress.emit(10, "Preparing data...")
            # 差异表达分析
            sc.tl.rank_genes_groups(
                self.adata, 
                groupby='leiden',
                groups=[self.group1], 
                reference=self.group2
            )
            
            self.progress.emit(100, "Analysis complete!")
            
            results = {
                'genes': self.adata.uns['rank_genes_groups'],
                'group1': self.group1,
                'group2': self.group2
            }
            
            self.finished.emit(results)
            
        except Exception as e:
            self.finished.emit({'error': str(e)})

class DifferentialExpressionModule(BaseGUIModule):
    analysis_completed = Signal(dict)
    
    @property
    def module_name(self) -> str:
        return "differential_expression"
    
    @property
    def display_name(self) -> str:
        return "差异表达分析"
    
    @property
    def description(self) -> str:
        return "计算不同细胞群之间的差异表达基因"
    
    @property
    def requirements(self) -> list:
        return ["scanpy", "pandas", "numpy"]
    
    def create_widget(self, parent=None):
        widget = QWidget(parent)
        layout = QVBoxLayout()
        
        # 控制面板
        controls_group = QGroupBox("分析参数")
        controls_layout = QGridLayout()
        
        controls_layout.addWidget(QLabel("群组1:"), 0, 0)
        self.group1_combo = QComboBox()
        controls_layout.addWidget(self.group1_combo, 0, 1)
        
        controls_layout.addWidget(QLabel("群组2:"), 1, 0)
        self.group2_combo = QComboBox()
        controls_layout.addWidget(self.group2_combo, 1, 1)
        
        self.run_btn = QPushButton("运行差异表达分析")
        self.run_btn.clicked.connect(self.run_analysis)
        self.run_btn.setEnabled(False)
        controls_layout.addWidget(self.run_btn, 2, 0, 1, 2)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 结果显示
        results_group = QGroupBox("结果")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        widget.setLayout(layout)
        self._widget = widget
        return widget
    
    def set_data(self, adata):
        self.adata = adata
        if adata is not None and 'leiden' in adata.obs.columns:
            # 更新群组选择器
            clusters = adata.obs['leiden'].unique()
            self.group1_combo.clear()
            self.group2_combo.clear()
            self.group1_combo.addItems(clusters)
            self.group2_combo.addItems(clusters)
            self.run_btn.setEnabled(True)
    
    def run_analysis(self):
        if self.adata is None:
            return
        
        group1 = self.group1_combo.currentText()
        group2 = self.group2_combo.currentText()
        
        if group1 == group2:
            QMessageBox.warning(self._widget, "错误", "请选择不同的群组")
            return
        
        # 开始分析
        self.progress_bar.setVisible(True)
        self.run_btn.setEnabled(False)
        
        self.worker = DEAnalysisWorker(self.adata, group1, group2)
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.progress.connect(self.update_progress)
        self.worker.start()
    
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.statusBar().showMessage(message)
    
    def on_analysis_finished(self, results):
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        
        if 'error' in results:
            QMessageBox.critical(self._widget, "分析失败", results['error'])
            return
        
        # 显示结果
        self.display_results(results)
        self.analysis_completed.emit(results)
    
    def display_results(self, results):
        # 在表格中显示差异表达基因
        genes_data = results['genes']
        # 实现结果显示逻辑...
        pass
```

## 总结

通过这个模块化系统，你可以：

1. **独立开发**：专注于你的分析逻辑，不用担心界面集成
2. **快速集成**：创建一个文件，自动集成到主界面
3. **松散耦合**：模块间通过标准接口通信
4. **易于维护**：每个模块都是独立的，便于调试和更新

这种架构让SingleCellStudio能够快速扩展新功能，同时保持代码的清晰和可维护性。 