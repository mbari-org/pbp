"""
Backward compatibility module for logging_helper.

This module has been moved to pbp.util.logging_helper.
Import from the new location in new code.
"""

import warnings

warnings.warn(
    "pbp.logging_helper is deprecated. Use pbp.util.logging_helper instead.",
    DeprecationWarning,
    stacklevel=2,
)

from pbp.util.logging_helper import create_logger, create_logger_info  # noqa: E402

__all__ = ["create_logger", "create_logger_info"]
