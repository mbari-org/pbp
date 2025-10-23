# GitHub Workflows

This directory contains automated CI/CD workflows for the mbari-pbp project.

## Workflows

### `ci.yml` - Continuous Integration
Runs tests, formatting checks, linting, and type checking on every push and pull request.

### `release-pypi.yml` - PyPI Release
Automatically builds and publishes the package to PyPI when a version tag is pushed (e.g., `v1.8.4`).

### `release-standalone.yml` - Standalone Distributions
Builds standalone executables for macOS, Linux, and Windows and uploads them to GitHub Releases.

## Using the Standalone Release Workflow

### Automatic Release

When you create a new release tag, the workflow automatically:
1. Builds standalone executables for all three platforms in parallel
2. Creates zip files with the format: `mbari-pbp-{version}-standalone-{platform}-{arch}.zip`
3. Uploads them to the GitHub Release

**To trigger a release:**

```bash
# Update version in pyproject.toml first, then:
just tag-and-push
```

This will create and push a tag like `v1.8.4`, which triggers both PyPI and standalone release workflows.

### Manual Testing

You can also trigger the workflow manually from the GitHub Actions tab to test builds without creating a release.
The artifacts will be available for download from the workflow run page for 7 days.

### What Gets Built

For each platform, the workflow creates a zip file containing:
- `mbari-pbp-standalone/pbp` (or `pbp.exe` on Windows) - The main executable
- `mbari-pbp-standalone/_internal/` - Bundled dependencies
- `mbari-pbp-standalone/README.md` - Project README
- `mbari-pbp-standalone/QUICKSTART.txt` - Platform-specific usage instructions

### Distribution

The zip files are automatically attached to the GitHub Release at:
```
https://github.com/mbari-org/pbp/releases/tag/v{version}
```

Users can download the appropriate zip for their platform, extract it,
and run the `pbp` executable without any Python installation.

### Platform Details

- **Linux**: Builds on `ubuntu-latest` (glibc-based, compatible with most modern Linux distributions)
- **macOS**: Builds on `macos-latest` (universal binary compatible with recent macOS versions)
- **Windows**: Builds on `windows-latest` (64-bit executable)

### System Dependencies

The workflow automatically installs required system dependencies:
- **Linux**: `libsndfile1` (via apt)
- **macOS**: `libsndfile` (via brew)
- **Windows**: No additional dependencies needed (bundled with soundfile)

### Troubleshooting

If a build fails:
1. Check the Actions tab for detailed logs
2. Verify that `pbp.spec` is compatible with the target platform
3. Ensure all dependencies are properly declared in `pyproject.toml`
4. Test locally using `just build_standalone`

### File Sizes

Typical zip file sizes:
- Linux: ~220-250 MB
- macOS: ~230-260 MB
- Windows: ~240-270 MB

These sizes include Python interpreter, all dependencies, and the application code.
