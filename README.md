# PyPAM based data processing

- [x] parse json files
- [x] process associated audio files
    - [x] iteration segment by segment
    - [x] concatenate segments for timekeeping
    - [x] invoke pypam per segment
    - [x] aggregate results
    - [x] frequency and psd array output between 10 and 10^5 Hz
    - [x] generate NetCDF and CSV
    - [x] preliminary inclusion of "effort" (number of seconds per minute)
- [x] cloud processing


## Development

I usually capture and use command recipes in a [`justfile`](justfile).

### Setup

```shell
python3 -m venv virtenv
source virtenv/bin/activate
just setup
```

At this point I typically run the unit tests while putting together the code:

```shell
just test
```

as well as others including:
```shell
just pylint
just dev
just to-gizo
```

**NOTE**: Before committing/pushing any changes, I make sure to run:

```shell
just all
```
```shell
python -m mypy .
Success: no issues found in 11 source files
python -m pytest
========================================= test session starts =========================================
platform darwin -- Python 3.9.12, pytest-7.2.2, pluggy-1.0.0
rootdir: /Users/carueda/github/mbari-org/pypam-based-processing
plugins: syrupy-4.0.1
collected 4 items

tests/test_json_support.py ..                                                                   [ 50%]
tests/test_misc.py ..                                                                           [100%]

--------------------------------------- snapshot report summary ---------------------------------------
8 snapshots passed.
========================================== 4 passed in 0.56s ==========================================
python -m ufmt format .
✨ 10 files already formatted ✨
python -m pylint src

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)
```
which includes testing, formatting, and pylint.
