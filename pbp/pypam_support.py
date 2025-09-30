"""
Backward compatibility module for pypam_support.

This module has been moved to pbp.hmb_gen.pypam_support.
Import from the new location in new code.
"""

import warnings

warnings.warn(
    "pbp.pypam_support is deprecated. Use pbp.hmb_gen.pypam_support instead.",
    DeprecationWarning,
    stacklevel=2,
)

from pbp.hmb_gen.pypam_support import ProcessResult, PypamSupport  # noqa: E402

__all__ = ["ProcessResult", "PypamSupport"]
