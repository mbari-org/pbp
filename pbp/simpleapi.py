"""
Backward compatibility module for simpleapi.

This module has been moved to pbp.hmb_gen.simpleapi.
Import from the new location in new code.
"""

import warnings

warnings.warn(
    "pbp.simpleapi is deprecated. Use pbp.hmb_gen.simpleapi instead.",
    DeprecationWarning,
    stacklevel=2,
)

from pbp.hmb_gen.simpleapi import HmbGen  # noqa: E402
from pbp.hmb_gen.process_helper import ProcessDayResult  # noqa: E402

__all__ = ["HmbGen", "ProcessDayResult"]
