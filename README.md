[![MBARI](https://www.mbari.org/wp-content/uploads/2014/11/logo-mbari-3b.png)](http://www.mbari.org)

[![main](https://github.com/mbari-org/pbp/actions/workflows/ci.yml/badge.svg)](https://github.com/mbari-org/pbp/actions/workflows/ci.yml)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/mbari-pbp)](https://pypi.org/project/mbari-pbp/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/language-Python-blue.svg)](https://www.python.org/downloads/)

# PyPAM based data processing

The [mbari-pbp](https://pypi.org/project/mbari-pbp/) package allows to
process ocean audio data archives to daily analysis products of hybrid millidecade spectra using
[PyPAM](https://github.com/lifewatch/pypam/).

**Status**: Functional version, including support for cloud based processing.

- [x] JSON generation of timekeeping with indication of start and duration of recognized sound files
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

Example plot of a daily hybrid millidecade generated with the [`pbp-hmb-plot`](https://docs.mbari.org/pbp/pbp-hmb-plot/)  command:
![](pbp-doc/docs/img/NRS11_20200101_sm.jpg)

## Documentation

Official documentation is available at
[docs.mbari.org/pbp](https://docs.mbari.org/pbp/).

## Installation

Please see <https://docs.mbari.org/pbp/#installation>.

## Programs and API

The mbari-pbp package includes command line interface (CLI) programs,
and also provides APIs you can use in your Python scripts or notebooks.

### CLI Programs

The package includes the following CLI programs:

| Program                                                    | Description                             |
|------------------------------------------------------------|-----------------------------------------|
| [`pbp-meta-gen`](https://docs.mbari.org/pbp/pbp-meta-gen/) | Generate JSON files with audio metadata |
| [`pbp-hmb-gen`](https://docs.mbari.org/pbp/pbp-hmb-gen/)   | Main HMB generation program             |
| [`pbp-cloud`](https://docs.mbari.org/pbp/pbp-cloud/)       | Program for cloud based processing      |
| [`pbp-hmb-plot`](https://docs.mbari.org/pbp/pbp-hmb-plot/) | Utility program to plot HMB product     |

### API

API documentation is available at [docs.mbari.org/pbp/api](https://docs.mbari.org/pbp/api/).

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

## Development

Interested in contributing? Please see [DEVELOPMENT.md](./DEVELOPMENT.md) for details.
