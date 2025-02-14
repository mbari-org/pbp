The `pbp-meta-gen` command-line program is used to generate JSON files with audio metadata. This is a necessary step 
before running the main HMB generation program to extract and optionally correct the time data.   

This also generates an overview of the recording coverage for the specified date range which
can be used to identify gaps in the data, help with the selection of the data to be processed,
or to identify any issues with the data before processing.

Instructions  below assume you have already installed the package,
e.g. `pip install mbari-pbp`.
Once this is done, you can proceed to the main program [pbp-hmb-gen](../pbp-hmb-gen).

## Overview

Three types of audio recorders are supported: NRS, IcListen, and Soundtrap files. Here is the current supported matrix:

----------------
| Recorder | [Google Storage](https://cloud.google.com/storage/docs/buckets) | [AWS S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) | Local Storage |
|----------|-----------------------------------------------------------------|------------------|---------------|
| NRS      |  :material-check:                                                               |  :material-close:               |  :material-check:             |
| IcListen |  :material-close:                                                               |  :material-check:               | :material-check:             |
| Soundtrap|  :material-close:                                                               |  :material-check:               | :material-check:             |
 

For audio that is stored in a cloud storage bucket, the URI that is required to access the audio files depends on the cloud storage provider.
The data must be stored in a public cloud storage bucket; private buckets are not supported.

- For Google Storage, use the gs: prefix, e.g. `gs://noaa-passive-bioacoustic/nrs/audio/11/nrs_11_2019-2021/audio`.
- For AWS S3, use the s3: prefix, e.g. `s3://pacific-sound-256khz`. 
- For local files, the URI is the path to the directory where the audio files are stored with the file: prefix, e.g. `file:///Volumes/PAM_Archive/FK01`, or  `file:\\Users\dcline\PAM_Archive\FK01`
!!! tip end "Note the triple slash after the prefix for a local archive file:///Volumes. This is required for the URI to be parsed correctly."


## Examples

!!! note prefix
    The prefix for any file, is the string that is used to match the beginning of the file name before the timestamp. For example, if the file name is `ONMS_FK01_7412_20230315_000000.wav`,
    the prefix would be `ONMS_FK01_7412_` or `ONMS_FK01_7412`, `NRS11_20191024_022220.flac` would have a prefix of `NRS11_`, and 
    `MARS_20220902_000000.wav` would have a prefix of `MARS_` or `MARS`.
     
    There is flexible handling of the timestamp in the file name, so any of following file names are all valid:

    ```
        NRS11_20191024_022220.flac
        NRS11_191024T022220Z.flac
        NRS11_20191024T022220Z.wav
        NRS11_20191024022220.wav
        NRS11_20191024T022220Z.d100.x.wav
        NRS11_191024T022220Z.d100.x.wav
    ```


## Generate JSONs with audio metadata from NRS flac files for a date range

The following command generates JSON files  in the `json/nrs` directory only for files in  `gs://noaa-passive-bioacoustic/nrs/audio/11/nrs_11_2019-2021/audio` 
that iclude the file string NRS11. Logs will be stored in the `output` directory, for the specified date range.
 

```shell
pbp-meta-gen --recorder=NRS \
             --json-base-dir=json/nrs \
             --output-dir=output \
             --uri=gs://noaa-passive-bioacoustic/nrs/audio/11/nrs_11_2019-2021/audio \
             --start=20191023 \
             --end=20191024 \
             --prefix=NRS11_
```

If your data is stored locally on Windows, e.g. in your `\Users\dcline\Downloads` directory, the command might look something like:

```shell
pbp-meta-gen --recorder NRS --json-base-dir=json/nrs \
             --output-dir=output \
             --uri= file:\\Users\dcline\Downloads\ \
             --start=20191023 \
             --end=20191024 \
             --prefix=NRS11_
```

Following this command, you should see two JSON files in the `json/nrs` directory; one for each day of the date range.

```text
json/nrs/
└── 2019
    ├── 20191023.json
    └── 20191024.json
    
output/
├── NRS20191023_20191024.log

```

## Generate JSONs with audio metadata from IcListen wav files for a date range

The following command generates JSON files in the `json/iclisten` directory only for files in `s3://pacific-sound-256khz` that include the file string MARS. 
Logs will be stored in the `output` directory, for the specified date range. The MARS data is recorded in 10-minute intervals, so there are many files to process.  

This would be a good time to go get a cup of coffee :coffee:. This will take a while to process since
the pacific sound archive has many files.

```shell
pbp-meta-gen --recorder=ICLISTEN \
             --json-base-dir=json/iclisten \
             --output-dir=output \
             --uri=s3://pacific-sound-256khz \
             --start=20191023 \
             --end=20191024 \
             --prefix=MARS
```

You should see two JSON files in the `json/iclisten` directory; one for each day of the date range.

```text
json/iclisten/
└── 2019
    ├── 20191023.json
    └── 20191024.json

output/
├── ICLISTEN20191023_20191024.log
```

## Generate JSONs with audio metadata from Soundtrap wav files for a date range

```shell
pbp-meta-gen --recorder=SOUNDTRAP \
            --json-base-dir=json/FK01 \
            --output-dir=logs/json/FK01 \
            --uri=file://Volumes/PAM_Archive/FK01 \
            --start=20230315 \
            --end=20230316 \
            --prefix=ONMS_FK01_7412
```

## JSON format

!!! note "Why JSON?"
    We choose JSON files to store the metadata because it is human-readable, easy to parse, and can be easily integrated as part of a 
    larger data processing pipeline. 

The JSON file schema is as follows:

----------------
| Field | Description                                                                                                                       |
|-------|-----------------------------------------------------------------------------------------------------------------------------------|
| channels | The number of channels in the audio file.                                                                                         |
| uri | The location of the audio file.  This is a URI that can be used to access the file in a *public* cloud storage bucket or local file system. |
| start | The start time of the audio file in ISO 8601 format.                                                                              |
| end | The end time of the audio file in ISO 8601 format.                                                                                |
| duration_secs | The duration of the audio file in seconds.                                                                                  |

```json
[
    {
        "uri": "gs://noaa-passive-bioacoustic/nrs/audio/11/nrs_11_2019-2021/audio/NRS11_20191023_222213.flac",
        "start": "2019-10-23T22:22:13Z",
        "end": "2019-10-24T02:22:13Z",
        "duration_secs": 14400,
        "channels": 1
    }
]
```

## Need help? Try the --help option 

```shell
$ pbp-meta-gen --help
```
```text
usage: pbp-meta-gen [-h] [--version] --recorder {NRS,ICLISTEN,SOUNDTRAP} --json-base-dir dir --output-dir dir --uri uri --start YYYYMMDD --end YYYYMMDD --prefix PREFIX [PREFIX ...]

Generate JSONs with audio metadata for NRS flac files, IcListen wav files, and Soundtrap wav files from either a local directory or gs/s3 bucket.

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --recorder {NRS,ICLISTEN,SOUNDTRAP}
                        Choose the audio instrument type
  --json-base-dir dir   JSON base directory to store the metadata
  --output-dir dir      Output directory to store logs
  --uri uri             Location of the audio files. S3 location supported for IcListen or Soundtrap, and GS supported for NRS.
  --start YYYYMMDD      The starting date to be processed.
  --end YYYYMMDD        The ending date to be processed.
  --prefix PREFIX [PREFIX ...]
                        Prefix for search to match the audio files. Assumption is the prefix is separated by an underscore, e.g. 'MARS_'.

Examples:
    pbp-meta-gen \
                 --json-base-dir=tests/json/nrs \
                 --output-dir=output \
                 --uri=s3://pacific-sound-ch01 \
                 --start=20220902 \
                 --end=20220902 \
                 --prefix=MARS \
                 --recorder=NRS

```