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
poetry run mypy .
Success: no issues found in 35 source files
poetry run pytest
================================== test session starts ======================
platform darwin -- Python 3.11.9, pytest-7.4.4, pluggy-1.5.0
rootdir: /Users/carueda/github/mbari-org/soundscape-repos/pbp
configfile: pyproject.toml
testpaths: tests
plugins: syrupy-4.6.1, cov-4.1.0
collected 16 items

tests/test_file_helper.py .                                           [  6%]
tests/test_json_support.py ...                                        [ 25%]
tests/test_meta_generator.py .....                                    [ 56%]
tests/test_metadata.py ...                                            [ 75%]
tests/test_misc.py ..                                                 [ 87%]
tests/test_simpleapi.py ..                                            [100%]

==================================== warnings summary =======================
....
-------------------------------- snapshot report summary --------------------
10 snapshots passed.
======================= 16 passed, 1 warning in 113.42s (0:01:53) ===========
poetry run ruff format .
36 files left unchanged
poetry run ruff check --fix
```
