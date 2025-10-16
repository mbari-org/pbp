#!/bin/bash
#
# Build standalone executable for mbari-pbp
#
# This creates a single executable that bundles all dependencies.
# Users can run the executable without installing Python or conda.
#

set -e

echo "=========================================="
echo "Building mbari-pbp standalone executable"
echo "=========================================="
echo

# Ensure pyinstaller is installed
echo "Installing/updating PyInstaller..."
poetry install --with dev
echo

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/
echo

# Build the executable
echo "Building executable with PyInstaller..."
poetry run pyinstaller pbp.spec
echo

# Show result
if [ -d "dist/pbp" ]; then
    echo "=========================================="
    echo "Build successful!"
    echo "=========================================="
    echo
    echo "Distribution created in: dist/pbp/"
    echo
    echo "Directory size:"
    du -sh dist/pbp
    echo
    echo "Executable:"
    ls -lh dist/pbp/pbp 2>/dev/null || ls -lh dist/pbp/pbp.exe 2>/dev/null
    echo
else
    echo "ERROR: Build failed - dist/pbp/ directory not found"
    exit 1
fi

# Create distribution package
echo ""
echo "Creating distribution package..."
rm -rf mbari-pbp-standalone
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

# Create zip file with platform info
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
VERSION=$(poetry version -s)
ZIPFILE="mbari-pbp-${VERSION}-standalone-${PLATFORM}-${ARCH}.zip"

echo ""
echo "Creating zip file: $ZIPFILE"
zip -r -q "$ZIPFILE" mbari-pbp-standalone/

echo ""
echo "=========================================="
echo "Distribution package created!"
echo "=========================================="
echo ""
echo "Archive: $ZIPFILE"
ls -lh "$ZIPFILE"
echo ""
echo "Users can extract and use with:"
echo "  unzip $ZIPFILE"
echo "  export PATH=\"\$PATH:\$(pwd)/mbari-pbp-standalone\""
echo "  pbp --help"
echo ""
