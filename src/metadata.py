# TODO revert to direct use of collections.OrderedDict as a type
#  when gizo has python >= 3.9 (because: "Type subscription requires python >= 3.9")
from typing import Any, Optional, OrderedDict as TOrderedDict
from collections import OrderedDict

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

    def set_global_attribute(self, attribute_name: str, value: Any):
        self._global_attrs[attribute_name] = value

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
