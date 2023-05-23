Calibration information about serial number 6716
(by following related queries in pyhydrophone for SoundTrap):

Get basic info:
```shell
curlie https://oceaninstruments.azurewebsites.net/api/Devices/Search/6716 | jq . > chumash/6716_devices.json
```
This seems to return all devices, but the entry with `"serialNo": "6716"` is:
```json
{
  "deviceId": 5181,
  "serialNo": "6716",
  "modelId": 15,
  "hpSerial": null,
  "modelName": "SoundTrap 600 HF"
}
```
With that `deviceId`, get calibration info:
```shell
curlie https://oceaninstruments.azurewebsites.net/api/Calibrations/Device/5181 | jq . > chumash/6716_calibration_.json
```
which includes:
```json
"lowFreq": 188.4,
"highFreq": 176,
```

Of course, the idea is to use PyHydrophone to fetch the relevant calibration info.
Per the SoundTrap class there, one will need no only the `serial_number`,
but also the `model` and `gain_type` (plus probably other parameters too).
Also, this issue is relevant: <https://github.com/lifewatch/pyhydrophone/issues/5>.

---

Initial basic testing processing Chumash heritage NMS data.

```shell
just main-cloud-chumash-basic-test
```
- performs downloading from S3, but no uploading, just for local inspection of generated files.
- files captured under `cloud_tmp_chumash/` (not committed to git).
- Not whole day processing but just a few of segments, also for initial inspection.

--- 

Some initial inspection of relevant files:

- `2023/`
  A small subset of the JSON files:
  ```shell
   aws s3 sync s3://pacific-sound-metadata/ch01/ . --exclude '*' --include '2023/202301*'
   ```

- Wav file listing:
  ```shell
  aws s3 ls s3://pacific-sound-ch01/ > wav_listing.txt
  ```
