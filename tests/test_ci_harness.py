from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_critical_files_exist() -> None:
    assert (REPO_ROOT / "src/analysis/pipeline.py").exists()
    assert (REPO_ROOT / "src/gui/professional_main_window.py").exists()
    assert (REPO_ROOT / "pytest.ini").exists()
    assert (REPO_ROOT / "src/cli/run_pipeline.py").exists()


def test_pipeline_contains_harmony_guard_and_diagnostics() -> None:
    text = (REPO_ROOT / "src/analysis/pipeline.py").read_text(encoding="utf-8")
    assert "import harmonypy" in text
    assert "integration_diagnostics.json" in text
    assert "_compute_integration_diagnostics" in text
    assert "batch_mixing_score" in text
    assert "checkpoint_mode" in text
    assert "run_context.json" in text


def test_professional_ui_contains_reproducibility_exports() -> None:
    text = (REPO_ROOT / "src/gui/professional_main_window.py").read_text(encoding="utf-8")
    assert "def save_project(" in text
    assert "def save_project_as(" in text
    assert "def export_analysis_data(" in text
    assert "def export_plots(" in text
    assert "def _build_project_manifest(" in text


def test_python_sources_compile() -> None:
    cmd = [
        "python",
        "-m",
        "compileall",
        str(REPO_ROOT / "src/analysis/pipeline.py"),
        str(REPO_ROOT / "src/gui/professional_main_window.py"),
        str(REPO_ROOT / "src/cli/run_pipeline.py"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
