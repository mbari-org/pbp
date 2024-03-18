# Development

Routine command recipes are captured in a [`justfile`](justfile),
to be run with the handy [`just`](https://github.com/casey/j) tool,
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
Success: no issues found in 25 source files
poetry run pytest
========================================= test session starts =========================================
platform darwin -- Python 3.9.17, pytest-7.4.4, pluggy-1.4.0
rootdir: ....
plugins: syrupy-4.6.1, cov-4.1.0
collected 12 items

tests/test_file_helper.py .                                                                     [  8%]
tests/test_json_generator.py ss.                                                                [ 33%]
tests/test_json_support.py ...                                                                  [ 58%]
tests/test_metadata.py ...                                                                      [ 83%]
tests/test_misc.py ..                                                                           [100%]

--------------------------------------- snapshot report summary ---------------------------------------
9 snapshots passed.
==================================== 10 passed, 2 skipped in 3.89s ====================================
ruff format .
34 files left unchanged
ruff check --fix
```
