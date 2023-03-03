WIP: Preparations for pypam-based data processing ...

Roughly:

- [x] parse json files
- [ ] process associated audio files
    - [x] iteration segment by segment
    - [x] concatenate segments for timekeeping
    - [ ] invoke pypam per segment
    - [ ] aggregate results
- [ ] cloud processing
- [ ] ...


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
```text
collected 3 items

tests/test_json_support.py ..                                                                            [ 66%]
tests/test_misc.py .                                                                                     [100%]

------------------------------------------- snapshot report summary --------------------------------------------
8 snapshots passed.
============================================== 3 passed in 0.12s ==============================================
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
which includes testing, formatting, and pylint.
