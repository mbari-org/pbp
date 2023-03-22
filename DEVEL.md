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
python3 -m venv virtenv
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
Success: no issues found in 14 source files
python -m pytest
=================================== test session starts ====================================
platform darwin -- Python 3.9.12, pytest-7.2.2, pluggy-1.0.0
...
plugins: syrupy-4.0.1
collected 5 items

tests/test_file_helper.py .                                                          [ 20%]
tests/test_json_support.py ..                                                        [ 60%]
tests/test_misc.py ..                                                                [100%]

--------------------------------- snapshot report summary ----------------------------------
8 snapshots passed.
==================================== 5 passed in 0.87s =====================================
python -m ufmt format .
✨ 12 files already formatted ✨
python -m pylint src

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)
```
