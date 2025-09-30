"""
Backward compatibility module for process_helper.

This module has been moved to pbp.hmb_gen.process_helper.
Import from the new location in new code.
"""

import warnings

warnings.warn(
    "pbp.process_helper is deprecated. Use pbp.hmb_gen.process_helper instead.",
    DeprecationWarning,
    stacklevel=2,
)

from pbp.hmb_gen.process_helper import (  # noqa: E402
    ProcessHelper,
    ProcessDayResult,
    DEFAULT_QUALITY_FLAG_VALUE,
    save_dataset_to_netcdf,
)

__all__ = [
    "ProcessHelper",
    "ProcessDayResult",
    "DEFAULT_QUALITY_FLAG_VALUE",
    "save_dataset_to_netcdf",
]
