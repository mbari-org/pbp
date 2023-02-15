#
# Some development recipes
# Use `just` - https://github.com/casey/just.
#

# List recipes
list:
    @just --list --unsorted

# A convenient recipe for development
dev: test format

# As the dev recipe plus pylint; good to run before committing changes
all: dev pylint

# Install dependencies
setup:
    pip3 install -r requirements.txt
    mypy --install-types

# Do static type checking (not very strict)
check:
    python -m mypy .

# Install std types for mypy
install-types:
    python -m mypy --install-types

# Do snapshot-update
snapshot-update:
    python -m pytest --snapshot-update

# Run tests
test *options="":
    python -m pytest {{options}}

# Format source code
format:
    python -m ufmt format .

# Format source code using ruff
ruff:
    ruff --fix .

# Run pylint
pylint:
    python -m pylint src

# With prior running of:
#   python -m pip install --upgrade build
# Create dist
dist:
    python -m build
