import pathlib

import click

from zerotk import deps
from zz.anatomy import AnatomyEngine
from zz.codegen import CodegenEngine


@deps.define
class CodegenCli:

    codegen = deps.Singleton(CodegenEngine)
    anatomy = deps.Singleton(AnatomyEngine)

    @deps.Command
    @click.argument("directory", type=click.Path(), default=".")
    def apply(self, directory: pathlib.Path = "."):
        self.codegen.run(directory)
        self.anatomy.run(directory)
