# PyPAM based data processing

This package uses [PyPAM](https://github.com/lifewatch/pypam/)
to generate _hybrid millidecade spectra_ for soundscape data.

**Status**: Functional version, including support for S3-based cloud based processing.

- [x] Timekeeping based on given JSON indicating start and duration of every available `.wav` file
- [x] Audio file processing
    - [x] Frequency and psd array output between 10 and 10^5 Hz
    - [x] Concatenation of processed 1-minute segments for daily product
    - [x] Calibration with given sensitivity file (NetCDF)
- [x] Data products
    - [x] NetCDF with metadata
    - [x] CSV (optionally)
- [x] Cloud processing (download inputs from, and upload generated products to S3)

TODO more details

## Refs

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

See [DEVEL.md](DEVEL.md) for details.
