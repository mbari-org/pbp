# PBP – PyPAM based processing

2024-07

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
