- `2023/`
  A small subset of the JSON files:
  ```shell
   aws s3 sync s3://pacific-sound-metadata/ch01/ . --exclude '*' --include '2023/202301*'
   ```
