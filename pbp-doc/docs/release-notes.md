# Release Notes

This page highlights significant updates and new features in PBP releases.
For detailed technical changes, see the [CHANGELOG.md](https://github.com/mbari-org/pbp/blob/main/CHANGELOG.md).
Please get in touch if you have any questions.

## 1.8.72 
(Nov 2025)

**Improvements**

- **Windows Path Handling**: Fixed issues with relative paths not being handled properly on Windows systems
- **Global Attributes**: Global attributes are now loaded and validated before processing begins,
  providing earlier error detection
- **Logging Enhancements**: Added detailed logging for path handling operations on Windows

## 1.8.6 
(Nov 2025)

**Bug Fixes**

- Improved error handling when processing global attribute replacements -
  now provides clearer diagnostic messages when issues occur

## 1.8.5 
(Oct 2025)

**Major Features**

**Unified CLI Interface**

The `pbp` command now provides a consistent interface for all PBP operations:

```shell
pbp meta-gen   # Generate JSON metadata files
pbp hmb-gen    # Generate HMB products
pbp hmb-plot   # Create visualization plots
pbp cloud      # Cloud-based processing
```

!!! tip "Migration Note"
    The previous direct commands (`pbp-meta-gen`, `pbp-hmb-gen`, etc.) still work in Conda installations
    for backward compatibility, but we recommend using the new `pbp <command>` style.

**Standalone Executables**

PBP is now available as standalone executables for Linux, macOS, and Windows - no Python installation required.

- Download from [GitHub Releases](https://github.com/mbari-org/pbp/releases)
- Extract and add to your PATH
- Run immediately - all dependencies included

This is ideal for:

- Field computers without Python
- Users unfamiliar with conda/pip
- Systems where dependency management is difficult
- Avoiding conflicts with other Python tools

See the [Installation](index.md#standalone) section for details.

**Improvements**

- **Plotting Enhancements**: Fixed handling of datasets without dusk/dawn periods (short time ranges)
- **Better Error Messages**: Standalone builds now provide clearer messages about feature limitations

## 1.8.2 
(Sep 2025)

**Bug Fixes**

- Restored API compatibility with backward compatibility shims
- Deprecation warnings guide users to new import paths
- Restored `create_logger_info` function used in existing notebooks

## 1.8.0 
(Sep 2025)

**Features**

**Flexible Time Resolution**

You can now specify custom time resolution for daily HMB processing:

```shell
pbp hmb-gen --time-resolution 60  # 1-minute resolution
```

**Auto-populated Global Attributes**

More metadata fields are now automatically populated, reducing manual configuration.

## 1.7.5 
(Sep 2025)

**Features**

**Direct File Processing**

Process individual audio files directly without requiring metadata JSON files:

```shell
pbp hmb-gen \
  --input-file /path/to/MARS_20250914_122000.wav \
  --timestamp-pattern "%Y%m%d_%H%M%S" \
  --time-resolution 1 \
  --voltage-multiplier 3 \
  --sensitivity-uri ./calibration.nc \
  --global-attrs ./global_attrs.yaml \
  --variable-attrs ./variable_attrs.yaml \
  --output-dir ./output
```

This is useful for:

- Quick processing of individual files
- Testing and validation
- Custom workflows without pre-generated metadata

New options:

- `--input-file` - Specify audio file to process
- `--timestamp-pattern` - Pattern to extract timestamp from filename
- `--time-resolution` - Time resolution in seconds

## 1.7.4 
(Aug 2025)

**Bug Fixes**

- Fixed regression that prevented CLI programs from running

## 1.7.1 
(Apr 2025)

**Improvements**

- Updated PyPAM dependency to version 0.3.2
- Bug fixes and stability improvements

## 1.6.4 
(Apr 2025)

**Features**

**Improved SoundTrap Metadata Extraction**

Metadata is now extracted directly from WAV headers instead of relying on companion XML files,
improving reliability and reducing external dependencies.

Thanks to @cparcerisas and @bram-cuyx for this contribution!

## 1.6.2 
(Mar 2025)

**Features**

**Quality Flag Support**

Add a quality flag variable to NetCDF output (fixed value of 2 - "Not Evaluated"):

```shell
pbp hmb-gen --add-quality-flag  # ... other options
```

Or via API:
```python
from pbp.hmb_gen import ProcessHelper

process_helper = ProcessHelper(
    add_quality_flag=True,  # Enable quality flag
    # ... other parameters
)
```

## 1.6.1 
(Mar 2025)

**Features**

**NetCDF Compression**

Generated NetCDF files are now compressed by default, significantly reducing file sizes.

To disable compression:

```shell
pbp hmb-gen --no-netcdf-compression  # ... other options
```

Or via API:
```python
process_helper = ProcessHelper(
    compress_netcdf=False,  # Disable compression
    # ... other parameters
)
```

## 1.4.3 
(Aug 2024)

**Improvements**

**Windows Compatibility**

PBP is now fully compatible with Windows systems. Thanks to @spacetimeengineer for this contribution!

## 1.4.2 
(Aug 2024)

**Breaking Changes**

**CLI Program Renaming**

For clarity and consistency, the CLI programs were renamed:

- `pbp` → `pbp-hmb-gen`
- `pbp-plot` → `pbp-hmb-plot`

!!! note
    These names were later unified under the `pbp` command in version 1.8.5.

## 1.4.1 
(Aug 2024)

**Features**

**S3 Unsigned Access**

Added support for accessing public S3 buckets without credentials:

```shell
pbp hmb-gen --s3-unsigned  # ... other options
```

## 1.2.5 
(Aug 2024)

**Features**

**Custom NetCDF Engine**

Specify which engine to use when opening NetCDF files:

```shell
pbp hmb-plot --engine h5netcdf  # ... other options
```

Default is `h5netcdf`.

## 1.2.0 
(Aug 2024)

**Breaking Changes**

**API Renaming**

The main API class was renamed for clarity:

```python
# Old (deprecated)
from pbp.simpleapi import Pbp

# New
from pbp.hmb_gen.simpleapi import HmbGen
```

## 1.1.1 
(Aug 2024)

**Features**

**Simplified High-Level API**

Introduced a new "porcelain" API to make PBP more user-friendly:

```python
from pbp.hmb_gen.simpleapi import HmbGen

hmb_gen = HmbGen()
hmb_gen.set_json_base_dir("/tmp/some_json_dir")
hmb_gen.set_output_dir("/tmp/output")
# ... other settings

# Check configuration
errors = hmb_gen.check_parameters()
if not errors:
    # Process a day
    result = hmb_gen.process_date('20201008')
    # Generate plot
    hmb_gen.plot_date('20201008')
```

This simplified interface makes it easier for users of all experience levels to get started.

## 1.0.9 
(July 2024)

**Bug Fixes**

- Fixed occasional issues with sound file caching

## 1.0.8 
(July 2024)

- First PyPI release.

## 0.3.0 
(Mar 2024)

- First PyPI pre-release.
