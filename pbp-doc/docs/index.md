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

You will use a shell (terminal on macOS or Linux, PowerShell on Windows)
to run audio data processing jobs using PBP.

We recommend installing PBP using [Conda](https://docs.conda.io/en/latest/).
If you already have Anaconda installed, you can use it.
If not, download and install [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/)
for your operating system.
Miniconda is all that is needed, and it is about one tenth the size of a full Anaconda installation.
After installation, on some systems, you can confirm that conda is available with:


```shell
which conda
```

Create a directory where you will install the PBP software,
for example: `/Users/YourUserName/pbp`.

Create an `environment.yml` file in the `pbp` directory, with this content:
```yaml
name: pbp
channels:
  - conda-forge
dependencies:
  - python=3.11
  - hdf5
  - netcdf4
  - libsndfile
  - pip
  - pip:
      - mbari-pbp
```

From within the terminal, while you are in your newly created pbp directory, issue this command:
```shell
conda env create
```

Activate your PBP processing environment with this command:
```shell
conda activate pbp
```

Notice that the prompt of the shell was augmented with `(pbp)` preceding the original prompt.

You can check the PBP version:
```shell
pbp-hmb-gen --version
```

You are now ready to process passive acoustic monitoring data to
[hybrid millidecade spectra](https://asa.scitation.org/doi/10.1121/10.0003324) using PBP.

Typically, within this top level directory for processing, you will also have a metadata directory
(calibration data for hydrophones, etc.), and scripts for processing (shell scripts or python scripts).
PBP creates some directory structures as needed during initial operation
(json directory for storing temporal metadata for processing jobs).


### Updating PBP

To update PBP to the latest version, while your `pbp` conda environment is activated, run this command:
```shell
pip install --upgrade mbari-pbp
```

If changes are needed to the conda environment (for example, new dependencies), after revising the `environment.yml` file,
you can update the `pbp` conda environment with this command:
```shell
conda env update
```

If you want to install the package from source and have already installed with the `pip install mbari-pbp` command,
you can install the package from source with the following command. This will get the latest version :construction: from the main branch.
```shell
pip install --no-cache-dir --force-reinstall git+https://github.com/mbari-org/pbp.git
```

## Programs

The package includes the following CLI programs:

| Program                                 | Description                                    |
|-----------------------------------------|------------------------------------------------|
| [`pbp-meta-gen`](pbp-meta-gen/index.md) | Generate JSON files with audio metadata.       |
| [`pbp-hmb-gen`](pbp-hmb-gen/index.md)   | Main HMB generation program.                   |
| [`pbp-cloud`](pbp-cloud/index.md)       | Program for cloud based processing.            |
| [`pbp-hmb-plot`](pbp-hmb-plot/index.md) | Utility program to plot resulting HMB product. |

 
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
