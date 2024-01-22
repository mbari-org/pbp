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

```shell
python3.9 -m venv virtenv
source virtenv/bin/activate
j setup
```

While working on the code, you want to keep all unit testing green:
```shell
j test
```

**NOTE**: Before committing/pushing any changes, make sure to run:
```shell
j all
```
which includes type checking, testing, formatting, and pylint:
```text
python -m mypy .
Success: no issues found in 23 source files
python -m pytest
==================================== test session starts =====================================
platform darwin -- Python 3.9.17, pytest-7.4.4, pluggy-1.0.0
...
plugins: anyio-4.0.0, syrupy-4.6.0, cov-4.1.0
collected 9 items

tests/test_file_helper.py .                                                            [ 11%]
tests/test_json_support.py ...                                                         [ 44%]
tests/test_metadata.py ...                                                             [ 77%]
tests/test_misc.py ..                                                                  [100%]

---------------------------------- snapshot report summary -----------------------------------
9 snapshots passed.
===================================== 9 passed in 0.66s ======================================
python -m ufmt format .
✨ 22 files already formatted ✨
python -m pylint src

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)
```
