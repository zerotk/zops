import click

from zz.cli import aws
from zz.cli import codegen
from zz.cli import git
from zz.cli import tf


# @click.group()
# def main():
#     pass


# main.add_command(aws.main)
# main.add_command(tf.main)
# main.add_command(codegen.main)
# main.add_command(git.main)


def main():
    from zerotk.appliance import Command

    @Command.define
    class ZopsCli(Command):

        __requirements__ = Command.Requirements(
            codegen=codegen.CodegenCli,
            # tf=tf.TerraformCli,
        )

        @click.group()
        def main(self):
            pass

    cli = ZopsCli()
    cli.initialize_cli()
    return cli.main()
