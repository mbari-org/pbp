import pathlib
from typing import Any, OrderedDict

import xarray as xr

from src import info, save_dataset_to_netcdf
from src.metadata import MetadataHelper, parse_attributes

GLOBAL_ATTRS_URI = "metadata/mars/globalAttributes.yaml"
VARIABLE_ATTRS_URI = "metadata/mars/variableAttributes.yaml"


def update_metadata_for_file(nc_filename: str, overwrite: bool):
    md_helper = MetadataHelper(
        _load_attributes("global", GLOBAL_ATTRS_URI),
        _load_attributes("variable", VARIABLE_ATTRS_URI),
    )

    ds = xr.open_dataset(nc_filename, engine="h5netcdf")
    ds.close()

    ds_result = xr.Dataset(
        attrs=ds.attrs.copy(),
    )

    for var_name, var_data in ds.data_vars.items():
        print(f"  Updating metadata for variable: {var_name}")
        ds_result[var_name] = var_data.copy()

        md_helper.assign_variable_attributes(ds_result[var_name], var_name)

    # psd_da = ds.psd
    # psd_da["time"] = md_helper.assign_variable_attributes(psd_da["time"], "time")
    # # md_helper.add_variable_attributes(data_vars["effort"], "effort")
    # # md_helper.add_variable_attributes(data_vars["frequency"], "frequency")
    # # if "sensitivity" in data_vars:
    # #     md_helper.add_variable_attributes(data_vars["sensitivity"], "sensitivity")
    # # md_helper.add_variable_attributes(data_vars["psd"], "psd")
    #
    # data_vars = {
    #     "psd": psd_da,
    #     "effort": ds.effort,
    #     # "frequency": ds.frequency,
    # }
    # if ds.sensitivity is not None:
    #     data_vars["sensitivity"] = ds.sensitivity
    #
    # global_attrs = ds.attrs  # TODO
    # ds_result = xr.Dataset(
    #     data_vars=data_vars,
    #     attrs=global_attrs,
    # )

    updated_filename = (
        nc_filename.replace(".nc", "_md_updated.nc") if overwrite else nc_filename
    )
    if save_dataset_to_netcdf(ds_result, updated_filename):
        print(f"  Metadata updated in: {updated_filename}")


# Similar to ProcessHelper._load_attributes but simplified here to local files only.
def _load_attributes(what: str, filename: str) -> OrderedDict[str, Any]:
    info(f"Loading {what} attributes from {filename=}")
    with open(filename, "r", encoding="UTF-8") as f:
        return parse_attributes(f.read(), pathlib.Path(filename).suffix)


if __name__ == "__main__":
    import sys

    over_write = False
    nc_files = []

    if sys.argv[1] == "--overwrite":
        over_write = True
        nc_files = sys.argv[2:]
    else:
        nc_files = sys.argv[1:]

    if len(nc_files) == 0:
        print(f"usage: {sys.argv[0]} [--overwrite] <netcdf>... ")
        sys.exit(1)

    for nc_f in nc_files:
        print(f"Updating metadata for: {nc_f}")
        update_metadata_for_file(nc_f, over_write)
