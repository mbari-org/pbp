"""
Backward compatibility module for misc_helper.

This module has been moved to pbp.hmb_gen.misc_helper.
Import from the new location in new code.
"""

import warnings

warnings.warn(
    "pbp.misc_helper is deprecated. Use pbp.hmb_gen.misc_helper instead.",
    DeprecationWarning,
    stacklevel=2,
)

from pbp.hmb_gen.misc_helper import (  # noqa: E402
    parse_date,
    gen_hour_minute_second_times,
    map_prefix,
    brief_list,
    print_given_args,
)

__all__ = [
    "parse_date",
    "gen_hour_minute_second_times",
    "map_prefix",
    "brief_list",
    "print_given_args",
]
