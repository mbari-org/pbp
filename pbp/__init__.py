import os

import xarray as xr

from pbp.logging_helper import PbpLogger


def save_dataset_to_netcdf(logger: PbpLogger, ds: xr.Dataset, filename: str) -> bool:
    logger.info(f"  - saving dataset to: {filename}")
    try:
        ds.to_netcdf(
            filename,
            engine="h5netcdf",
            encoding={
                "effort": {"_FillValue": None},
                "frequency": {"_FillValue": None},
                "sensitivity": {"_FillValue": None},
            },
        )
        return True
    except Exception as e:  # pylint: disable=broad-exception-caught
        error = f"Unable to save {filename}: {e}"
        logger.error(error)
        print(error)
        return False


def save_dataset_to_csv(logger: PbpLogger, ds: xr.Dataset, filename: str):
    logger.info(f"  - saving dataset to: {filename}")
    try:
        ds.to_pandas().to_csv(filename, float_format="%.1f")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Unable to save {filename}: {e}")


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
