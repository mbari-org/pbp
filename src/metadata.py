# TODO revert to direct use of collections.OrderedDict as a type
#  when gizo has python >= 3.9 (because: "Type subscription requires python >= 3.9")
from collections import OrderedDict
from typing import Any, Dict, Optional, OrderedDict as TOrderedDict

import xarray as xr

from src.misc_helper import debug, error


class MetadataHelper:
    def __init__(
        self,
        global_attributes: Optional[TOrderedDict[str, Any]] = None,
        variable_attributes: Optional[TOrderedDict[str, Any]] = None,
    ):
        self._global_attrs: TOrderedDict[str, Any] = global_attributes or OrderedDict()
        self._var_attrs: TOrderedDict[str, Any] = variable_attributes or OrderedDict()

    def set_some_global_attributes(self, attrs: Dict[str, Any]):
        for k, v in attrs.items():
            self._global_attrs[k] = v

    def get_global_attributes(self) -> TOrderedDict[str, Any]:
        return self._global_attrs

    def add_variable_attributes(self, da: xr.DataArray, var_attribute_name: str):
        if var_attribute_name in self._var_attrs:
            keys = []
            for k, v in self._var_attrs[var_attribute_name].items():
                da.attrs[k] = v
                keys.append(k)
            debug(f"For variable '{var_attribute_name}', added attributes: {keys}")
        else:
            error(f"Unrecognized {var_attribute_name=}")


def replace_snippets(
    attributes: TOrderedDict[str, Any], snippets: Dict[str, str]
) -> TOrderedDict[str, Any]:
    """
    Replaces snippets in any entries with values of type string.
    :param attributes:
        Attribute dictionary to replace snippets in.
    :param snippets:
        Example: { "{{PyPAM_version}}": "0.2.0" }
    :return:
        A new dictionary with the snippets replaced.
    """
    result = OrderedDict()
    for k, v in attributes.items():
        if isinstance(v, str):
            for snippet, replacement in snippets.items():
                v = v.replace(snippet, replacement)
        result[k] = v
    return result
