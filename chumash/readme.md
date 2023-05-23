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
