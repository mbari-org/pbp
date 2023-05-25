import json
from typing import Any, Dict

import xarray as xr

from src.misc_helper import error

ATTRIBUTES_FILENAME = "metadata/attributes.json"

attributes: Dict[str, Any] = {}


def metadata_init():
    global attributes
    with open(ATTRIBUTES_FILENAME, "r", encoding="UTF-8") as f:
        attributes = json.load(f)


def add_attributes(da: xr.DataArray, attr_name: str):
    global attributes
    assert len(attributes), "init() must be called first"
    if attr_name in attributes:
        for k, v in attributes[attr_name].items():
            da.attrs[k] = v
    else:
        error(f"Unrecognized {attr_name=}")
