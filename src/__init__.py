import os

import xarray as xr

from src.misc_helper import info


def save_dataset_to_netcdf(ds: xr.Dataset, filename: str):
    info(f"  - saving dataset to: {filename}")
    ds.to_netcdf(filename, engine="h5netcdf", encoding={"time": {"dtype": "int64"}})


def save_dataset_to_csv(ds: xr.Dataset, filename: str):
    info(f"  - saving dataset to: {filename}")
    ds.to_pandas().to_csv(filename, float_format="%.1f")


def get_cpus_to_use(num_cpus: int) -> int:
    cpu_count: int = os.cpu_count() or 1
    if num_cpus <= 0 or num_cpus > cpu_count:
        num_cpus = cpu_count
    return num_cpus


class PBPException(Exception):
    """
    Placeholder for a more specific exception.
    """

    def __init__(self, msg: str):
        super().__init__(f"PBPException({msg})")
