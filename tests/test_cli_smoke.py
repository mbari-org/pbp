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
