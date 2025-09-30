"""
Backward compatibility module for hmb_metadata.

This module has been moved to pbp.hmb_gen.hmb_metadata.
Import from the new location in new code.
"""

import warnings

warnings.warn(
    "pbp.hmb_metadata is deprecated. Use pbp.hmb_gen.hmb_metadata instead.",
    DeprecationWarning,
    stacklevel=2,
)

from pbp.hmb_gen.hmb_metadata import (  # noqa: E402
    HmbMetadataHelper,
    parse_attributes,
    replace_snippets,
)

__all__ = [
    "HmbMetadataHelper",
    "parse_attributes",
    "replace_snippets",
]
