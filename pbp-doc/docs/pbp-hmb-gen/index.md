!!! danger "WIP"

# HMB Generation

`pbp-hmb-gen` is the main program for generating the HMB product.
It processes ocean audio data archives to daily analysis products of hybrid millidecade spectra using PyPAM.

The program accepts several options.
A typical use mainly involves the following:

| Option            | To indicate   |
| ----------------- |--------------- |
| `--json-base-dir` | base directory for JSON files                                                         |
| `--date`          | date to be processed                                                                  |
| `--global-attrs`  | URI of a YAML file with global attributes to be added to the NetCDF file              |
| `--variable-attrs`| URI of a YAML file with attributes to associate with the variables in the NetCDF file |
| `--output-dir`    | output directory                                                                      |
| `--output-prefix` | output filename prefix                                                                |
| `--subset-to`     | subset of the resulting PSD in terms of central frequency                             |

Also, the following depending on the recorder:

| Option                   | To indicate   |
| ------------------------ |--------------- |
| `--voltage-multiplier`   | applied on the loaded signal   |
| `--sensitivity-uri`      | URI of sensitivity NetCDF for calibration of result |
| `--sensitivity-flat-value`| flat sensitivity value to be used for calibration |


## Usage

```shell
$ pbp-hmb-gen --help
```
```text
usage: pbp-hmb-gen [-h] [--version] --json-base-dir dir [--audio-base-dir dir] [--global-attrs uri] [--set-global-attr key value] [--variable-attrs uri]
               [--audio-path-map-prefix from~to] [--audio-path-prefix dir] --date YYYYMMDD [--voltage-multiplier value] [--sensitivity-uri file]
               [--sensitivity-flat-value value] --output-dir dir [--output-prefix prefix] [--s3] [--s3-unsigned] [--gs] [--download-dir dir] [--assume-downloaded-files]
               [--retain-downloaded-files] [--max-segments num] [--subset-to lower upper]

Process ocean audio data archives to daily analysis products of hybrid millidecade spectra using PyPAM.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --json-base-dir dir   JSON base directory
  --audio-base-dir dir  Audio base directory. By default, none
  --global-attrs uri    URI of JSON file with global attributes to be added to the NetCDF file.
  --set-global-attr key value
                        Replace {{key}} with the given value for every occurrence of {{key}} in the global attrs file.
  --variable-attrs uri  URI of JSON file with attributes to associate to the variables in the NetCDF file.
  --audio-path-map-prefix from~to
                        Prefix mapping to get actual audio uri to be used. Example: 's3://pacific-sound-256khz-2022~file:///PAM_Archive/2022'.
  --audio-path-prefix dir
                        Ad hoc path prefix for sound file location, for example, /Volumes. By default, no prefix applied.
  --date YYYYMMDD       The date to be processed.
  --voltage-multiplier value
                        Applied on the loaded signal.
  --sensitivity-uri file
                        URI of sensitivity NetCDF for calibration of result. Has precedence over --sensitivity-flat-value.
  --sensitivity-flat-value value
                        Flat sensitivity value to be used for calibration.
  --output-dir dir      Output directory
  --output-prefix prefix
                        Output filename prefix
  --s3                  s3 access is involved, possibly with required credentials.
  --s3-unsigned         s3 access is involved, not requiring credentials.
  --download-dir dir    Directory for any downloads (e.g., when s3 or gs is involved).
  --assume-downloaded-files
                        If any destination file for a download exists, assume it was downloaded already.
  --retain-downloaded-files
                        Do not remove any downloaded files after use.
  --max-segments num    Test convenience: limit number of segments to process. By default, 0 (no limit).
  --subset-to lower upper
                        Subset the resulting PSD to [lower, upper), in terms of central frequency.

Examples:
    pbp-hmb-gen --json-base-dir=tests/json \
        --audio-base-dir=tests/wav \
        --date=20220902 \
        --output-dir=output
```