---
description: Process ocean audio data archives to daily analysis products of hybrid millidecade spectra using PyPAM.
---

!!! note "WIP"
    Thanks for your interest in PBP. This documentation is still a work in progress :construction:.
    Please get in touch if you have any questions or suggestions.

# MBARI PBP

The [`mbari-pbp`](https://pypi.org/project/mbari-pbp/) package allows to
process ocean audio data archives to daily analysis products of hybrid millidecade spectra using
[PyPAM](https://github.com/lifewatch/pypam/).

You can use PBP by directly running the included CLI the programs,
as well as a dependency in your own Python code.

**Features**:
  
- [x] Audio metadata extraction for managed timekeeping 
    - [x] Start and duration of recognized wav and flac sound files either locally or in cloud (JSON)
    - [x] Coverage plot of sound recordings
- [x] Audio file processing
    - [x] Frequency and psd array output
    - [x] Concatenation of processed 1-minute segments for daily product
    - [x] Calibration with given sensitivity file (NetCDF), or flat sensitivity value
- [x] Data products
    - [x] NetCDF with metadata
    - [x] Summary plot
- [x] Cloud processing
    - [x] Inputs can be downloaded from and uploaded to S3
    - [x] Inputs can be downloaded from public GCS bucket
    - [ ] Outputs can be uploaded to GCS

## Installation

On your environment the only requirement is Python 3.9, 3.10, or 3.11.[^1]
Make sure your Python installation includes the `pip` and `venv` modules,
or install them separately as needed.

You can run `python3 --version` to check the version of Python installed.

[^1]: As currently [required by PyPAM](https://github.com/lifewatch/pypam/blob/29e82f0c5c6ce43b457d76963cb9d82392740654/pyproject.toml#L16).

As a general practice, it is recommended to use a virtual environment for the installation.
```shell
python3.9 -m venv virtenv
source virtenv/bin/activate
```

Install the package:
```shell
pip install mbari-pbp
```

!!! note ""
    If you are upgrading from a previous version, you can use the following command:
    ```shell
    pip install --upgrade mbari-pbp
    ```

## Advanced Installation

If you want to install the package from source and have already installed with the `pip install mbari-pbp` command,
you can install the package from source with the following command. This will get the latest version :construction: from the main branch.

```shell
pip install --no-cache-dir --force-reinstall  git+https://github.com/mbari-org/pbp.git
```

## Programs

The package includes the following CLI programs:

| Program                         | Description                                    |
|---------------------------------|------------------------------------------------|
| [`pbp-meta-gen`](pbp-meta-gen/) | Generate JSON files with audio metadata.       |
| [`pbp-hmb-gen`](pbp-hmb-gen/)   | Main HMB generation program.                   |
| [`pbp-cloud`](pbp-cloud/)       | Program for cloud based processing.            |
| [`pbp-hmb-plot`](pbp-hmb-plot/) | Utility program to plot resulting HMB product. |

 
## References

- PyPAM - Python tool for Passive Acoustic Monitoring –
  <https://doi.org/10.5281/zenodo.6044593>
- Computation of single-sided mean-square sound pressure spectral density with 1 Hz resolution follows
  ISO 18405 3.1.3.13 (International Standard ISO 18405:2017(E), Underwater Acoustics – Terminology. Geneva: ISO)
  – https://www.iso.org/standard/62406.html
- Hybrid millidecade spectra: A practical format for exchange of long-term ambient sound data –
  <https://asa.scitation.org/doi/10.1121/10.0003324>
- Erratum: Hybrid millidecade spectra –
  <https://asa.scitation.org/doi/10.1121/10.0005818>
