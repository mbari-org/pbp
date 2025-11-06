import subprocess
import pytest

CLI_COMMANDS = [
    "pbp-meta-gen",
    "pbp-hmb-gen",
    "pbp-hmb-plot",
]


@pytest.mark.parametrize("command", CLI_COMMANDS)
def test_cli_help_works(command):
    """Test that CLI command shows help without error."""
    result = subprocess.run(
        [command, "--help"],
        capture_output=True,
        text=True,
        timeout=30,  # Prevent hanging
    )
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
