# Standalone Distribution

This document describes how to build and distribute standalone executables of
mbari-pbp.

**Note:** Standalone distributions for Linux, macOS, and Windows are
automatically built and published via GitHub Actions when a version tag is
pushed. See the [CI/CD Integration](#cicd-integration) section for details.

## Overview

The standalone build creates a single executable that includes:
- Python runtime
- All Python dependencies (pypam, numpy, scipy, etc.)
- All mbari-pbp tools as subcommands

Users can run the executable without installing Python, conda, or any
dependencies.

## Building

### Prerequisites

- Poetry installed
- Development environment set up (`poetry install --with dev`)

### Build Command

```bash
just build_standalone   # same as:  ./scripts/build_standalone.sh
```

Or manually:

```bash
poetry run pyinstaller pbp.spec
```

The distribution will be created in `dist/pbp/` directory containing the
executable and all dependencies.

## Usage

The standalone executable provides a unified CLI with subcommands:

```bash
# Add to PATH (or use full path)
export PATH="$PATH:/path/to/dist/pbp"

# Show help
pbp --help

# Run subcommands
pbp meta-gen --help
pbp hmb-gen --help
pbp hmb-plot --help
pbp cloud --help

# Or run directly without adding to PATH:
./dist/pbp/pbp --help
```

## Distribution

**Note:** For official releases, standalone distributions are automatically
created by the GitHub Actions workflow described in the
[CI/CD Integration](#cicd-integration) section. The instructions below are for
creating standalone builds locally during development or testing.

### Creating a Release Package

The build script automatically creates a distribution package with:
- The executable and bundled dependencies
- README.md
- QUICKSTART.txt with platform-specific usage instructions

The final zip file is named:
`mbari-pbp-{version}-standalone-{platform}-{arch}.zip`

### Platform-Specific Builds

You must build separately for each platform:

- **macOS Intel**: Build on macOS Intel machine
- **macOS Apple Silicon**: Build on macOS ARM machine (or use
  `--target-arch universal2`)
- **Linux**: Build on Linux machine (consider using Docker for reproducible
  builds)
- **Windows**: Build on Windows machine

### File Sizes

In the initial setup, distribution sizes (as zip files) were in the order of
200-300 MB per platform. The sizes vary due to platform-specific bundling and
compression of the Python runtime and scientific libraries (numpy, scipy, etc.).

The `--onedir` format provides faster startup (~1-2 seconds) compared to
`--onefile` (~3-5 seconds).

## Known Limitations

### Interactive Plotting

The `--show` and `--only-show` options in `pbp hmb-plot` are not available in
standalone builds due to missing interactive display backends. The executable
will display a user-friendly message suggesting to save plots to files instead.

### Matplotlib Font Cache

On first run, matplotlib will display a "building font cache" message. This is
harmless and should only happen once per session.

## Troubleshooting

### Missing Dependencies

If the executable fails with import errors, add the missing module to
`hiddenimports` in `pbp.spec`.

### Native Library Issues

Some dependencies (soundfile, h5netcdf) require native libraries. These should
be automatically detected and bundled. If issues occur:

1. Check PyInstaller output for warnings about missing libraries
2. Manually specify binaries in `pbp.spec` if needed

### Testing

Always test the standalone executable on a clean machine without Python
installed to ensure all dependencies are properly bundled.

## Technical Details

### Architecture

- Entry point: `pbp/main_cli.py` - Unified CLI with subcommand routing
  - Includes multiprocessing compatibility fixes for frozen executables
  - Detects frozen state using `sys.frozen` and `sys._MEIPASS` attributes
- Build config: `pbp.spec` - PyInstaller specification
- Build script: `scripts/build_standalone.sh` - Automated build process
- CI/CD: `.github/workflows/release-standalone.yml` - Automated multi-platform
  builds

### Benefits vs Traditional Installation

**Standalone Distribution:**
- ✅ No Python/conda installation required
- ✅ No dependency conflicts
- ✅ Fast startup (~1-2 seconds with --onedir)
- ✅ Simple: download, extract, add to PATH
- ❌ Large file size (200-300MB)
- ❌ Platform-specific builds needed

**Traditional Installation (pip/conda):**
- ✅ Smaller download size
- ✅ Easier to update
- ❌ Requires Python/conda knowledge
- ❌ Potential dependency conflicts
- ❌ More complex setup for non-technical users

## CI/CD Integration

Automated builds are configured in `.github/workflows/release-standalone.yml`.

The workflow:
- Triggers automatically on version tags (e.g., `v1.8.4`)
- Can be triggered manually from the GitHub Actions tab for testing
- Builds for Linux, macOS, and Windows in parallel
- Creates properly named zip files:
  `mbari-pbp-{version}-standalone-{platform}-{arch}.zip`
- Automatically uploads to GitHub Releases

**To create a new release with standalone builds:**

```bash
# Update version in pyproject.toml, then:
just tag-and-push
```

This triggers both PyPI publication and standalone builds.

See `.github/workflows/README.md` for detailed documentation.

## Acknowledgments

The standalone distribution capability is made possible by
[PyInstaller](https://pyinstaller.org/), a powerful tool for packaging Python
applications into standalone executables.

The implementation of the standalone build system, including the multiprocessing
compatibility fixes, GitHub Actions workflow, and documentation, was developed
with assistance from Claude (Anthropic's AI assistant).
