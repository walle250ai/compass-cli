from typer.testing import CliRunner

from compass.cli import app

runner = CliRunner()


def test_compass_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_compass_new_help():
    result = runner.invoke(app, ["new", "--help"])
    assert result.exit_code == 0


def test_compass_validate_help():
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0


def test_compass_pack_help():
    result = runner.invoke(app, ["pack", "--help"])
    assert result.exit_code == 0
