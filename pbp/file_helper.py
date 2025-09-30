"""
Backward compatibility module for file_helper.

This module has been moved to pbp.hmb_gen.file_helper.
Import from the new location in new code.
"""

import warnings

warnings.warn(
    "pbp.file_helper is deprecated. Use pbp.hmb_gen.file_helper instead.",
    DeprecationWarning,
    stacklevel=2,
)

from pbp.hmb_gen.file_helper import FileHelper  # noqa: E402

__all__ = ["FileHelper"]
