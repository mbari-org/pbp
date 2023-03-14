import os

import xarray as xr


def save_netcdf(milli_psd: xr.DataArray, filename: str):
    print(f"  - saving NetCDF: {filename}")
    milli_psd.to_netcdf(filename)
    # on my Mac: format='NETCDF4_CLASSIC' triggers:
    #    ValueError: invalid format for scipy.io.netcdf backend: 'NETCDF4_CLASSIC'


def save_csv(milli_psd: xr.DataArray, filename: str):
    print(f"  - saving    CSV: {filename}")
    milli_psd.to_pandas().to_csv(filename, float_format="%.1f")


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
