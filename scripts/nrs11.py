# As in the notebook: https://colab.research.google.com/drive/1RaFVZzdRt88gY1SR_J34XMdRLgBjEdI-

from pbp.hmb_gen.process_helper import ProcessHelper
from pbp.hmb_gen.file_helper import FileHelper
from pbp.logging_helper import create_logger

from google.cloud.storage import Client as GsClient

import xarray as xr
import dask
import pandas as pd
import time

json_base_dir = "NRS11/noaa-passive-bioacoustic_nrs_11_2019-2021"
global_attrs_uri = "NRS11/globalAttributes_NRS11.yaml"
variable_attrs_uri = "NRS11/variableAttributes_NRS11.yaml"

voltage_multiplier = 2.5
sensitivity_uri = "NRS11/NRS11_H5R6_sensitivity_hms5kHz.nc"
subset_to = (10, 2_000)

# Downloaded files are stored here while being processed:
download_dir = "NRS11/DOWNLOADS"

# Location for generated files:
output_dir = "NRS11/OUTPUT"
# A prefix for the name of generate files:
output_prefix = "NRS11_"


def process_date(date: str, gen_netcdf: bool = True):
    """
    Main function to generate the HMB product for a given day.

    It makes use of supporting elements in PBP in terms of logging,
    file handling, and PyPAM based HMB generation.

    :param date: Date to process, in YYYYMMDD format.

    :param gen_netcdf:  Allows caller to skip the `.nc` creation here
    and instead save the datasets after all days have been generated
    (see parallel execution below).

    :return: the generated xarray dataset.
    """

    log_filename = f"{output_dir}/{output_prefix}{date}.log"

    log = create_logger(
        log_filename_and_level=(log_filename, "INFO"),
        console_level=None,
    )

    # we are only downloading publicly accessible datasets:
    gs_client = GsClient.create_anonymous_client()

    file_helper = FileHelper(
        log=log,
        json_base_dir=json_base_dir,
        gs_client=gs_client,
        download_dir=download_dir,
    )

    process_helper = ProcessHelper(
        log=log,
        file_helper=file_helper,
        output_dir=output_dir,
        output_prefix=output_prefix,
        global_attrs_uri=global_attrs_uri,
        variable_attrs_uri=variable_attrs_uri,
        voltage_multiplier=voltage_multiplier,
        sensitivity_uri=sensitivity_uri,
        subset_to=subset_to,
    )

    ## now, get the HMB result:
    print(f"::: Started processing {date=}")
    result = process_helper.process_day(date)

    if gen_netcdf:
        nc_filename = f"{output_dir}/{output_prefix}{date}.nc"
        print(f":::   Ended processing {date=} =>  {nc_filename=}")
    else:
        print(f":::   Ended processing {date=} => (dataset generated in memory)")

    if result is not None:
        return result.dataset
    else:
        print(f"::: UNEXPECTED: no segments were processed for {date=}")


def process_multiple_dates(
    dates: list[str], gen_netcdf: bool = False
) -> list[xr.Dataset]:
    """
    Generates HMB for multiple days in parallel using Dask.
    Returns the resulting HMB datasets.

    :param dates: The dates to process, each in YYYYMMDD format.

    :param gen_netcdf:  Allows caller to skip the `.nc` creation here
    and instead save the datasets after all days have been generated.

    :return: the list of generated datasets.
    """

    @dask.delayed
    def delayed_process_date(date: str):
        return process_date(date, gen_netcdf=gen_netcdf)

    ## To display total elapsed time at the end the processing:
    start_time = time.time()

    ## This will be called by Dask when all dates have completed processing:
    def aggregate(*datasets):  # -> list[xr.Dataset]:
        elapsed_time = time.time() - start_time
        print(
            f"===> All {len(datasets)} dates completed. Elapsed time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} mins)"
        )
        return datasets

    ## Prepare the processes:
    delayed_processes = [delayed_process_date(date) for date in dates]
    aggregation = dask.delayed(aggregate)(*delayed_processes)

    ## And launch them:
    return aggregation.compute()


## Here, we set `dates` as the list of 'YYYYMMDD' dates we want to process:

## For just a few dates, we can define the list explicitly:
# dates = ['20200110', '20200111', '20200112']

## but in general we can use pandas to help us generate the list:
date_range = pd.date_range(start="2020-01-01", end="2020-01-05")
dates = date_range.strftime("%Y%m%d").tolist()

## Now, launch the generation:

print(f"Launching HMB generation for {len(dates)} {dates=}")

## NOTE: due to issues observed when concurrently saving the resulting netCDF files,
## this flag allows to postpone the saving for after all datasets have been generated:
gen_netcdf = False

## Get all HMB datasets:
generated_datasets = process_multiple_dates(dates, gen_netcdf=gen_netcdf)

print(f"Generated datasets: {len(generated_datasets)}\n")

if not gen_netcdf:
    # so, we now do the file saving here:
    print("Saving generated datasets...")
    for date, ds in zip(dates, generated_datasets):
        nc_filename = f"{output_dir}/{output_prefix}{date}.nc"
        print(f"  Saving {nc_filename=}")
        try:
            ds.to_netcdf(
                nc_filename,
                engine="netcdf4",
                encoding={
                    "effort": {"_FillValue": None},
                    "frequency": {"_FillValue": None},
                    "sensitivity": {"_FillValue": None},
                },
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Unable to save {nc_filename}: {e}")
