from zz.cli import aws
from zz.cli import codegen
from zz.cli import git
from zz.cli import tf


def main():
    from zerotk.appliance import Command

    @Command.define
    class ZopsCli(Command):

        __requirements__ = Command.Requirements(
            codegen=codegen.CodegenCli,
            tf=tf.TerraformCli,
            git=git.GitCli,
            aws=aws.AwsCli,
        )

    cli = ZopsCli()
    return cli.main()
