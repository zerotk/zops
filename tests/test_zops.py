import click
from click.testing import CliRunner
from zerotk.zops import cli


def test_zops():
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.output == 'HELP\n'
