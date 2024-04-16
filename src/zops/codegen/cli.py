import click

import zops.codegen.cli_commands as commands


@click.group(name="codegen")
def main():
    """
    Code generation.
    """


main.add_command(commands.codegen_new_apply)
main.add_command(commands.codegen_apply)
