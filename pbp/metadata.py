import json
from collections import OrderedDict
from typing import Any, Dict, Optional

import xarray as xr
import yaml


def parse_attributes(contents: str, suffix: str) -> OrderedDict[str, Any]:
    """
    Parses given contents into a dictionary of attributes.
    :param contents:
        String with valid JSON or YAML contents.
    :param suffix:
        Used to determine the content format.
    :return:
        The parsed attributes.
    """
    if suffix == ".json":
        return json.loads(contents, object_pairs_hook=OrderedDict)
    if suffix in (".yaml", ".yml"):
        return yaml.load(contents, Loader=yaml.SafeLoader)
    raise ValueError(f"Unrecognized contents for format: {suffix}")


class MetadataHelper:
    def __init__(
        self,
        log,  # : loguru.Logger,
        global_attributes: Optional[OrderedDict[str, Any]] = None,
        variable_attributes: Optional[OrderedDict[str, Any]] = None,
    ):
        self.log = log
        self._global_attrs: OrderedDict[str, Any] = global_attributes or OrderedDict()
        self._var_attrs: OrderedDict[str, Any] = variable_attributes or OrderedDict()

    def set_some_global_attributes(self, attrs: Dict[str, Any]):
        for k, v in attrs.items():
            self._global_attrs[k] = v

    def get_global_attributes(self) -> OrderedDict[str, Any]:
        return self._global_attrs

    def add_variable_attributes(self, da: xr.DataArray, var_attribute_name: str):
        if var_attribute_name in self._var_attrs:
            keys = []
            for k, v in self._var_attrs[var_attribute_name].items():
                da.attrs[k] = v
                keys.append(k)
            self.log.debug(
                f"For variable '{var_attribute_name}', added attributes: {keys}"
            )
        else:
            self.log.error(f"Unrecognized {var_attribute_name=}")


def replace_snippets(
    attributes: OrderedDict[str, Any], snippets: Dict[str, str]
) -> OrderedDict[str, Any]:
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
