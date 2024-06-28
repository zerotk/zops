from zz.cli import aws
from zz.cli import codegen
from zz.cli import git
from zz.cli import tf


def main():
    from zerotk import deps

    @deps.define
    class ZopsCli:

        codegen = deps.Command(codegen.CodegenCli)
        tf = deps.Command(tf.TerraformCli)
        git = deps.Command(git.GitCli)
        aws = deps.Command(aws.AwsCli)

    cli = ZopsCli()
    return cli.main()
