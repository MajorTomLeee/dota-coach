from click.testing import CliRunner
from dotacoach.cli import main

def test_help():
    r = CliRunner().invoke(main, ["--help"])
    assert r.exit_code == 0
    assert "run" in r.output
    assert "weekly" in r.output
    assert "install-gsi" in r.output
