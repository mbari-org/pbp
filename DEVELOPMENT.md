# Development

Routine command recipes are captured in a [`justfile`](justfile),
to be run with the handy [`just`](https://just.systems/) tool,
which I alias to `j` in my shell.

Run:
```shell
j
```
to see the available recipes (and look at [`justfile`](justfile) for more details).

### Setup

Upon a fresh clone:
```shell
j setup
```

Upon updating dependencies:
```shell
j update-deps
```

While working on the code, you want to keep all unit testing green:
```shell
j test
```

**NOTE**: Before committing/pushing any changes, make sure to run:
```shell
j all
```
which includes type checking, testing, and formatting and linting with ruff:
```text
poetry run ruff format .
54 files left unchanged
poetry run ty check
All checks passed!
poetry run pytest
===================== test session starts =========================
platform darwin -- Python 3.11.11, pytest-7.4.4, pluggy-1.6.0
rootdir: /Users/carueda/github/mbari-org/soundscape-repos/pbp
configfile: pyproject.toml
testpaths: tests
plugins: syrupy-4.6.1, cov-4.1.0
collected 44 items

tests/test_cli_smoke.py ....                                  [  9%]
tests/test_get_bucket_key_simple.py .                         [ 11%]
tests/test_hmb_metadata.py ...                                [ 18%]
tests/test_json_support.py ...                                [ 25%]
tests/test_meta_generator.py .....                            [ 36%]
tests/test_misc.py ...                                        [ 43%]
tests/test_simpleapi.py ..                                    [ 47%]
tests/test_uri_handler.py .......................             [100%]

------------------- snapshot report summary ------------------------
13 snapshots passed.
=================== 44 passed in 99.34s (0:01:39) ==================
poetry run ruff check --fix
```
