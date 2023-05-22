- `2023/`
  A small subset of the JSON files:
  ```shell
   aws s3 sync s3://pacific-sound-metadata/ch01/ . --exclude '*' --include '2023/202301*'
   ```

- Wav file listing:
  ```shell
  aws s3 ls s3://pacific-sound-ch01/ > wav_listing.txt
  ```
  
