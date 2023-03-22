# PyPAM based data processing

This package uses [PyPAM](https://github.com/lifewatch/pypam/)
to generate _hybrid millidecade spectra_ for Soundscape data.

**Status**: Initial functional version, including cloud based processing.

- [x] JSON file ingestion according to initial structure
- [x] Audio file processing
    - [x] Timekeeping
    - [x] Frequency and psd array output between 10 and 10^5 Hz
    - [x] Concatenation of processed 1-minute segments for daily product
    - [x] Calibration with given sensitivity file (NetCDF)
    - [x] NetCDF and CSV data products
    - [x] Preliminary inclusion of "effort" (number of used seconds per minute)
- [x] Cloud processing (download of inputs from, and upload of generated products to S3)

TODO more details

## Refs

- Python tool for Passive Acoustic Monitoring -
  <https://github.com/lifewatch/pypam/>
- Ocean Sound Analysis Software for Making Ambient Noise Trends Accessible (MANTA) -
  <https://www.frontiersin.org/articles/10.3389/fmars.2021.703650/full>
- Hybrid millidecade spectra -
  <https://asa.scitation.org/doi/10.1121/10.0003324>
- Erratum: Hybrid millidecade spectra
  <https://asa.scitation.org/doi/10.1121/10.0005818>

## Development

See [DEVEL.md](DEVEL.md) for details.
