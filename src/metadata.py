from typing import Any, Dict, Optional

import xarray as xr

from src.misc_helper import error


class MetadataHelper:
    def __init__(
        self,
        global_attributes: Optional[Dict[str, Any]] = None,
        variable_attributes: Optional[Dict[str, Any]] = None,
    ):
        self._global_attrs: Dict[str, Any] = global_attributes or {}
        self._var_attrs: Dict[str, Any] = variable_attributes or {}

    def set_global_attribute(self, attribute_name: str, value: Any):
        self._global_attrs[attribute_name] = value

    def get_global_attributes(self) -> Dict[str, Any]:
        return self._global_attrs

    def add_variable_attributes(self, da: xr.DataArray, var_attribute_name: str):
        if var_attribute_name in self._var_attrs:
            for k, v in self._var_attrs[var_attribute_name].items():
                da.attrs[k] = v
        else:
            error(f"Unrecognized {var_attribute_name=}")
