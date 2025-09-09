import pathlib
import click

from zerotk import deps
from zz.aag import AagEngine


@deps.define
class AagCli:

    aag = deps.Singleton(AagEngine)

    @click.command
    @click.argument("playbook_filename", type=click.Path(), default=".")
    def apply(self, playbook_filename: pathlib.Path = "."):
        """
        Apply AAG configuration in the specified file.
        """
        self.aag.run(playbook_filename)
