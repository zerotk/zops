import pathlib

from zerotk.appliance import Command
from zz.anatomy import AnatomyEngine
from zz.codegen import CodegenEngine
import click


@Command.define
class CodegenCli(Command):

    __requirements__ = Command.Requirements(
        codegen=CodegenEngine,
        anatomy=AnatomyEngine,
    )

    @click.command()
    @click.argument("directory", type=click.Path())
    def run(self, directory: pathlib.Path = "."):
        self.codegen.run(directory)
        self.anatomy.run(directory)

    def other(self):
        pass
