# Development

Routine command recipes are captured in a [`justfile`](justfile),
to be run with  [`just`](https://just.systems/) tool.

Run:
```shell
just
```
to see the available recipes (and look at [`justfile`](justfile) for more details).

### Setup

Upon a fresh clone:
```shell
just setup
```

Upon updating dependencies:
```shell
just update-deps
```

While working on the code, you want to keep all unit testing green:
```shell
just test
```

**NOTE**: Before committing/pushing any changes, make sure to run:
```shell
just all
```
which includes type checking, testing, and formatting and linting with ruff:
```text
poetry run ruff format .
56 files left unchanged
poetry run ty check
All checks passed!
poetry run pytest
===================== test session starts =========================
platform darwin -- Python 3.11.11, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/carueda/github/mbari-org/soundscape-repos/pbp
configfile: pyproject.toml
testpaths: tests
plugins: syrupy-4.9.1
collected 59 items

tests/test_cli_smoke.py ....                                  [  6%]
tests/test_get_bucket_key_simple.py .                         [  8%]
tests/test_hmb_metadata.py ...                                [ 13%]
tests/test_hmb_regression.py ..............                   [ 37%]
tests/test_json_support.py ...                                [ 42%]
tests/test_meta_generator.py ......                           [ 52%]
tests/test_misc.py ...                                        [ 57%]
tests/test_simpleapi.py ..                                    [ 61%]
tests/test_uri_handler.py .......................             [100%]

------------------- snapshot report summary ------------------------
17 snapshots passed.
=================== 59 passed, 1 warning in 112.07s (0:01:52) ==================
poetry run ruff check --fix
```
