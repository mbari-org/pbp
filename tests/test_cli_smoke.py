import subprocess
from subprocess import CompletedProcess

import pytest


def _run_process(args: list[str]) -> CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=30,  # Prevent hanging
    )


def test_cli_help_works():
    """Test that CLI entry point shows help without error."""
    result = _run_process(["pbp", "--help"])
    assert result.returncode == 0, f"--help failed with: {result.stderr}"
    assert len(result.stdout) > 0, "--help produced no output"


CLI_COMMANDS = [
    "meta-gen",
    "hmb-gen",
    "hmb-plot",
]


@pytest.mark.parametrize("command", CLI_COMMANDS)
def test_cli_command_help_works(command):
    """Test that CLI command shows help without error."""
    result = _run_process(["pbp", command, "--help"])
    assert result.returncode == 0, f"{command} --help failed with: {result.stderr}"
    assert len(result.stdout) > 0, f"{command} --help produced no output"


def test_hmb_gen_multiprocessing_flags_in_help():
    """Test that multiprocessing flags appear in pbp-hmb-gen help."""
    result = subprocess.run(
        ["pbp-hmb-gen", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "--no-multiprocessing" in result.stdout
    assert "--num-workers" in result.stdout
