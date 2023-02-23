WIP: Preparations for pypam-based data processing ...

Roughly:

- [x] parse json files
- [ ] process associated audio files
    - [ ] initially minute by minute to invoke pypam
- [ ] cloud processing
- [ ] ...


```shell
python3 -m venv virtenv
source virtenv/bin/activate
pip3 install -r requirements.txt
pip3 install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ lifewatch-pypam
```

```shell
python src/main.py | head
```
```text
TenMinEntry(path='/PAM_Archive/2022/09/MARS_20220901_235016.wav', duration_secs=600.0, end=datetime.datetime(2022, 9, 2, 0, 0, 16), channels=1, jitter=0)
TenMinEntry(path='/PAM_Archive/2022/09/MARS_20220902_000016.wav', duration_secs=600.0, end=datetime.datetime(2022, 9, 2, 0, 10, 16), channels=1, jitter=0)
TenMinEntry(path='/PAM_Archive/2022/09/MARS_20220902_001016.wav', duration_secs=600.0, end=datetime.datetime(2022, 9, 2, 0, 20, 16), channels=1, jitter=0)
TenMinEntry(path='/PAM_Archive/2022/09/MARS_20220902_002016.wav', duration_secs=600.0, end=datetime.datetime(2022, 9, 2, 0, 30, 16), channels=1, jitter=0)
TenMinEntry(path='/PAM_Archive/2022/09/MARS_20220902_003016.wav', duration_secs=600.0, end=datetime.datetime(2022, 9, 2, 0, 40, 16), channels=1, jitter=0)
TenMinEntry(path='/PAM_Archive/2022/09/MARS_20220902_004016.wav', duration_secs=600.0, end=datetime.datetime(2022, 9, 2, 0, 50, 16), channels=1, jitter=0)
TenMinEntry(path='/PAM_Archive/2022/09/MARS_20220902_005016.wav', duration_secs=600.0, end=datetime.datetime(2022, 9, 2, 1, 0, 16), channels=1, jitter=0)
TenMinEntry(path='/PAM_Archive/2022/09/MARS_20220902_010016.wav', duration_secs=600.0, end=datetime.datetime(2022, 9, 2, 1, 10, 16), channels=1, jitter=0)
TenMinEntry(path='/PAM_Archive/2022/09/MARS_20220902_011016.wav', duration_secs=600.0, end=datetime.datetime(2022, 9, 2, 1, 20, 16), channels=1, jitter=0)
TenMinEntry(path='/PAM_Archive/2022/09/MARS_20220902_012016.wav', duration_secs=600.0, end=datetime.datetime(2022, 9, 2, 1, 30, 16), channels=1, jitter=0)
```
