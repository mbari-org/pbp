# PBP – PyPAM based processing

2024-12

- The setup and sources for the end-user documentation site has been incorporated in this repo.

2024-09

- 1.5.1: released (09/23)
- 1.5.0:
    - bringing up recent updates
    - a minor fix in a log.debug statement
    - also noting that 1.4.9 was published but still with 1.4.8 in pyproject.toml

- 1.4.5:
    - removed unneeded print at end of `plot_date` such that the resulting plot in the notebook
      is not affected in terms of requiring undesirable scrolling (hopefully).
  
- 1.4.4: Maintenance release.

2024-08

- 1.4.3: Adjustments to make pbp-meta-gen and pbp-hmb-gen Windows compatible.
  Thanks to @spacetimeengineer for the contribution!

- 1.4.2:
    - renamed `pbp` CLI program to `pbp-hmb-gen` 
    - renamed `pbp-plot` CLI program to `pbp-hmb-plot` 

- 1.4.1 - HMB generation CLI now with `--s3-unsigned` option to use unsigned config.

- 1.4.0 with improved "meta-gen" functionality

- 1.3.0 while retying clean publishing to pypi
- 1.2.8 - just a bit of cleanup, including removal of the release-docker workflow.
  (dockerization is happening elsewhere, but doing it here can be revisited later).
- 1.2.7 mainly to test new release-pypi action

- 1.2.6 adjust python dep to `python = ">=3.9,<3.12.0"`
 
- 1.2.5 `pbp-plot` now explicitly uses `h5netcdf` when calling `xarray.open_dataset`. 
  But a new option `--engine name` allows to specify the engine to use.

- 1.2.3 `HmbGen` adjustments:
    - `check_parameters` now returns `str | None`, with string indicating any errors.
    - `process_date` now returns `ProcessDayResult | str`, with string indicating any errors. 

- 1.2.2 Fix for new `set_print_downloading_lines`
- 1.2.1 Complementary to the usual logging options, added `set_print_downloading_lines(bool)`
  to `HmbGen` so one can get "downloading <uri>" lines printed to the console.
  Also, exposed other similar options provided by underlying `FileHelper` in `HmbGen`:
  `set_assume_downloaded_files(bool)`, `set_retain_downloaded_files(bool)`.

2024-08

- 1.2.0 renamed `Pbp` class to `HmbGen` to be more specific

    ```python
    from pbp.simpleapi import HmbGen
    hmb_gen = HmbGen()
    hmb_gen.set_json_base_dir("/tmp/some_json_dir")
    hmb_gen.set_... # other settings
    hmb_gen.check_parameters()
    # all ok, proceed:
    hmb_gen.process_date('20201008')
    hmb_gen.plot_date('20201008')
    ```

- 1.1.1 release introducing a new "porcelain" API intended to make our package even
  more user-friendly. This high-level interface simplifies the usage of the package
  for common scenarios, particularly those that are less complex, enabling users
  of all experience levels to get started more easily.


2024-07

- 1.0.9/10 release with fix to occasional issue dealing with sound file cache.
- new release, with 1.0.8 for both the package and the docker image.
  We will keep these two aligned (at least to the minor version).
- new package release 0.3.0b19 (`just publish`)
  and git tagging (v1.0.7) for corresponding docker image release.
  TODO: as probably already mentioned somewhere, we should harmonize the versioning.
  We could simply continue with our own versioning, independent of that of PyPAM. 
 
- fixed mypy issues by adding types-six and types-pytz to the dependencies
- Fixed the issue with the  migration to `loguru` which broke the json generation code
- Added missing logic to capture a file overlapping the end day boundary which was lost in code changes in April 2024
- Fixed the ending time calculation for ICListen wav files which was incorrectly being set to the start time of the same file 
- Other minor renames and code cleanup for clarity in the json generation code
- Added support for xtracing metadata for Soundtrap files that look like ONMS_FK01_7412_20230314_204134.log.xml
- Better support for extracing metadata for HARP files

2024-06

- did new pypi release to fix links, etc., and in preparation to
  generate corresponding new version of docker image.
- did the pending "pypam-based-processing" to "pbp" renaming.
  The ones related with docker may need review.

2024-04

- added `scripts/nrs11.py`, basically as in the batch notebook.
  Can be run under this repo with: `poetry run python scripts/nrs11.py`
- make sure loggers are independent of each other (one per processing day).
  Annoyingly, `loguru.Logger` type hint is not recognized when running in the command line,
  so commenting out that for now. 
- Use loguru for logging.
  Main reason is that separate configuration of the console and the file outputs continued proving tricky
  with the standard logging, which resulted in unexpected log levels when running in notebooks.
- Adjusted logging to be less verbose

2024-03

- For global attributes, now resolving the `{{PyPAM_version}}` snippet against the
  actual version number (according to `importlib.metadata`).
  Also added a `{{PBP_version}}` snippet in case we eventually want to use it.
- removed `--gen-csv` option (not really used/needed)
- added `--version` option to the programs
- minor code reorg
- enabled poetry
    - now packaging and publishing to PyPI 
    - TODO ongoing: README/justfile adjustments, etc. 
- added this ChangeLog.


----

See git commit history for details.

2023-02 - Initial commit
