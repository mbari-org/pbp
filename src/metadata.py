import json
from typing import Any, Dict

import xarray as xr

from src.misc_helper import error

VAR_ATTRIBUTES_FILENAME = "metadata/var_attributes.json"

var_attributes: Dict[str, Any] = {}


def metadata_init():
    global var_attributes
    with open(VAR_ATTRIBUTES_FILENAME, "r", encoding="UTF-8") as f:
        var_attributes = json.load(f)


def add_variable_attributes(da: xr.DataArray, var_attribute_name: str):
    assert len(var_attributes), "init() must be called first"
    if var_attribute_name in var_attributes:
        for k, v in var_attributes[var_attribute_name].items():
            da.attrs[k] = v
    else:
        error(f"Unrecognized {var_attribute_name=}")
