!!! note
    This is a placeholder for the documentation of the `pbp-cloud` command-line program.

# Processing in the cloud


## The `pbp-cloud` program
                                                        
TODO: proper description of the `pbp-cloud` program.

For now, the following directly adapted from the source code:

----

TODO Adjustments for GCS as the program is still only focused on S3.


By cloud based processing we basically mean the ability
to get input files (json and wav) from S3 and write output files to S3.

All program parameters are to be passed via environment variables:

- `DATE`: (Required)
     The date to process. Format: "YYYYMMDD".
- `S3_JSON_BUCKET_PREFIX`: (Optional)
     Bucket prefix to be used to locate the YYYYMMDD.json file
     By default, `s3://pacific-sound-metadata/256khz`.
- `S3_OUTPUT_BUCKET`: (Optional)
     The bucket to write the generated output to.
     Typically, this is to be provided, but it is optional to facilitate testing.
- `OUTPUT_PREFIX`: (Optional)
     Output filename prefix. By default, `milli_psd_`.
     The resulting file will be named as `<OUTPUT_PREFIX><DATE>.nc`.
- `GLOBAL_ATTRS_URI`: (Optional)
     URI of JSON file with global attributes to be added to the NetCDF file.
- `VARIABLE_ATTRS_URI`: (Optional)
     URI of JSON file with attributes to associate with the variables in the NetCDF file.
- `VOLTAGE_MULTIPLIER`: (Optional)
     Applied on the loaded signal.
- `SENSITIVITY_NETCDF_URI`: (Optional)
     URI of sensitivity NetCDF file that should be used to calibrate the result.
- `SENSITIVITY_FLAT_VALUE`: (Optional)
     Flat sensitivity value to be used for calibration
     if `SENSITIVITY_NETCDF_URI` is not given.
- `SUBSET_TO`: (Required)  Format: `lower,upper`.
     Subset the resulting PSD to `[lower, upper)`, in terms of central frequency.

TODO: retrieve sensitivity information using PyHydrophone when none
     of the `SENSITIVITY_*` environment variables above are given.

Mainly for testing purposes, also these environment variables are inspected:

- `CLOUD_TMP_DIR`: (Optional)
     Local workspace for downloads and for generated files to be uploaded.
     By default, `cloud_tmp`.

- `MAX_SEGMENTS`: (Optional)
     0, the default, means no restriction, that is, all segments for each day
     will be processed.

- `ASSUME_DOWNLOADED_FILES`: (Optional)
     If "yes", then if any destination file for a download exists,
     it is assumed downloaded already.
     The default is that downloads are always performed.

- `RETAIN_DOWNLOADED_FILES`: (Optional)
     If "yes", do not remove any downloaded files after use.
     The default is that any downloaded file is removed after use.


## Running on AWS

TODO: Describe how to run the program on AWS.

## Running on GCP

TODO: Describe how to run the program on GCP.
