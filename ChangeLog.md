# PBP – PyPAM based processing

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
