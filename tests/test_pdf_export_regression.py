from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


PLOTS_PATH = Path(__file__).resolve().parents[1] / 'src' / 'visualization' / 'plots.py'
spec = spec_from_file_location('plots_module_for_test', PLOTS_PATH)
plots_module = module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(plots_module)

_save_figure_with_pdf = plots_module._save_figure_with_pdf


def test_save_helper_creates_pdf_companion_for_png_path(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])

    png_path = tmp_path / 'umap_plot.png'
    _save_figure_with_pdf(fig, str(png_path))

    assert png_path.exists(), 'Requested PNG file was not created'
    assert png_path.with_suffix('.pdf').exists(), 'PDF companion file was not created'

    plt.close(fig)


def test_save_helper_pdf_path_writes_single_pdf(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [1, 0])

    pdf_path = tmp_path / 'summary_plot.pdf'
    _save_figure_with_pdf(fig, str(pdf_path))

    assert pdf_path.exists(), 'Requested PDF file was not created'
    assert len(list(tmp_path.glob('*.pdf'))) == 1

    plt.close(fig)
