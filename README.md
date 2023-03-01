WIP: Preparations for pypam-based data processing ...

Roughly:

- [x] parse json files
- [ ] process associated audio files
    - [x] iteration segment by segment
    - [ ] invoke pypam per segment
    - [ ] aggregate results
- [ ] cloud processing
- [ ] ...


```shell
python3 -m venv virtenv
source virtenv/bin/activate
pip3 install -r requirements.txt
pip3 install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ lifewatch-pypam
```

```shell
python -m pytest
```
```text
tests/test_json_parsing.py .                                                 [ 50%]
tests/test_misc.py .                                                         [100%]

----------------------------- snapshot report summary ------------------------------
4 snapshots passed.
================================ 2 passed in 0.07s =================================
```
