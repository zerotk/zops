"""
Click group `tf` with all commands.
"""

import click

from . import cli_commands


@click.group(name="tf")
def main():
    """
    Terraform-related commands.
    """


main.add_command(cli_commands.tf_plan)
