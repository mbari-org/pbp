"""
Backward compatibility module for plotting.

This module has been moved to pbp.hmb_plot.plotting.
Import from the new location in new code.
"""

import warnings

warnings.warn(
    "pbp.plotting is deprecated. Use pbp.hmb_plot.plotting instead.",
    DeprecationWarning,
    stacklevel=2,
)

from pbp.hmb_plot.plotting import plot_dataset_summary  # noqa: E402

__all__ = ["plot_dataset_summary"]
