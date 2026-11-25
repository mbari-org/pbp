import sys

from pbp.hmb_plot.main_plot import parse_arguments
from pbp.hmb_plot.plot_const import DEFAULT_TITLE


def test_default_title_has_no_extra_quotes(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["pbp-hmb-plot", "some.nc"])
    assert parse_arguments().title == DEFAULT_TITLE
