# Standalone Distribution

This document describes how to build and distribute standalone executables of mbari-pbp.

## Overview

The standalone build creates a single executable that includes:
- Python runtime
- All Python dependencies (pypam, numpy, scipy, etc.)
- All mbari-pbp tools as subcommands

Users can run the executable without installing Python, conda, or any dependencies.

## Building

### Prerequisites

- Poetry installed
- Development environment set up (`poetry install --with dev`)

### Build Command

```bash
./scripts/build_standalone.sh
```

Or manually:

```bash
poetry run pyinstaller pbp.spec
```

The distribution will be created in `dist/pbp/` directory containing the executable and all dependencies.

## Usage

The standalone executable provides a unified CLI with subcommands:

```bash
# Add to PATH (or use full path)
export PATH="$PATH:/path/to/dist/pbp"

# Show help
pbp --help

# Run subcommands
pbp hmb-gen --help
pbp cloud --help
pbp hmb-plot --help
pbp meta-gen --help

# Example: Generate HMB
pbp hmb-gen --uri s3://bucket/data --date 2024-01-01

# Or run directly without adding to PATH:
./dist/pbp/pbp --help
```

## Distribution

### Creating a Release Package

1. Build the executable for each target platform (macOS, Linux, Windows)
2. Create a distribution package:

```bash
# Copy the distribution directory
cp -r dist/pbp mbari-pbp-standalone
cp README.md mbari-pbp-standalone/

# Create quick start guide
cat > mbari-pbp-standalone/QUICKSTART.txt << 'EOF'
mbari-pbp Standalone Distribution
==================================

Quick Start:
1. Add the 'mbari-pbp-standalone' directory to your PATH:

   # For bash/zsh (add to ~/.bashrc or ~/.zshrc):
   export PATH="$PATH:/path/to/mbari-pbp-standalone"

   # Or use the full path:
   /path/to/mbari-pbp-standalone/pbp --help

2. Run any command:
   pbp --help
   pbp hmb-gen --help
   pbp cloud --help
   pbp hmb-plot --help
   pbp meta-gen --help

3. Example usage:
   pbp hmb-gen --uri s3://mybucket/audio --date 2024-01-01

For full documentation, visit:
https://docs.mbari.org/pbp/

EOF

# Create archive
zip -r mbari-pbp-standalone-macos-$(uname -m).zip mbari-pbp-standalone/
```

### Platform-Specific Builds

You must build separately for each platform:

- **macOS Intel**: Build on macOS Intel machine
- **macOS Apple Silicon**: Build on macOS ARM machine (or use `--target-arch universal2`)
- **Linux**: Build on Linux machine (consider using Docker for reproducible builds)
- **Windows**: Build on Windows machine

### File Sizes

Expect the distribution directory to be 200-400MB due to bundled Python runtime and scientific libraries (numpy, scipy, etc.). The `--onedir` format provides faster startup (~1-2 seconds) compared to `--onefile` (~3-5 seconds).

## Troubleshooting

### Missing Dependencies

If the executable fails with import errors, add the missing module to `hiddenimports` in `pbp.spec`.

### Native Library Issues

Some dependencies (soundfile, h5netcdf) require native libraries. These should be automatically detected and bundled. If issues occur:

1. Check PyInstaller output for warnings about missing libraries
2. Manually specify binaries in `pbp.spec` if needed

### Testing

Always test the standalone executable on a clean machine without Python installed to ensure all dependencies are properly bundled.

## Technical Details

### Architecture

- Entry point: `pbp/main_cli.py` - Unified CLI with subcommand routing
- Build config: `pbp.spec` - PyInstaller specification
- Build script: `scripts/build_standalone.sh` - Automated build process

### Benefits vs Traditional Installation

**Standalone Distribution:**
- ✅ No Python/conda installation required
- ✅ No dependency conflicts
- ✅ Fast startup (~1-2 seconds with --onedir)
- ✅ Simple: download, extract, add to PATH
- ❌ Large file size (200-400MB)
- ❌ Platform-specific builds needed

**Traditional Installation (pip/conda):**
- ✅ Smaller download size
- ✅ Easier to update
- ❌ Requires Python/conda knowledge
- ❌ Potential dependency conflicts
- ❌ More complex setup for non-technical users

## CI/CD Integration

Consider automating builds using GitHub Actions:

```yaml
name: Build Standalone

on:
  release:
    types: [created]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install poetry
      - run: poetry install --with dev
      - run: poetry run pyinstaller pbp.spec
      - uses: actions/upload-artifact@v3
        with:
          name: pbp-${{ matrix.os }}
          path: dist/pbp*
```
