"""CLI smoke tests."""

from click.testing import CliRunner

from justpipe.cli.main import cli


def test_cli_help_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "justpipe" in result.output.lower()


def test_cli_pipelines_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["pipelines", "--help"])
    assert result.exit_code == 0
    assert "pipeline" in result.output.lower()
