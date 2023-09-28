# PyPAM based data processing

This package uses [PyPAM](https://github.com/lifewatch/pypam/)
to generate _hybrid millidecade band spectra_ for soundscape data.

**Status**: Functional version, including support for S3-based cloud based processing.

- [x] Timekeeping based on given JSON indicating start and duration of every available `.wav` file
- [x] Audio file processing
    - [x] Frequency and psd array output
    - [x] Concatenation of processed 1-minute segments for daily product
    - [x] Calibration with given sensitivity file (NetCDF)
    - [x] Calibration with given flat sensitivity value
- [x] Data products
    - [x] NetCDF with metadata
    - [x] CSV (optional)
    - [x] Summary plot (optional)
- [x] Cloud processing (inputs downloaded from, and generated products uploaded to S3)

TODO more details

## Setup

### Create and activate virtual environment

    python3.9 -m venv virtenv
    source virtenv/bin/activate

### Install dependencies

    pip3 install -r requirements.txt
    pip3 install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ lifewatch-pypam==0.2.0

### Programs

- `src/main.py` - Main CLI program, run `python src/main.py --help` for usage.

- `src/main_cloud.py` - Main program for cloud based processing. 
   All parameters passed via environment variables, see source file.

- `src/plot.py` - Plotting program: `python src/plot.py --help`.


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
