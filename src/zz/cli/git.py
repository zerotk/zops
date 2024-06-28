import asyncio

import click

from zerotk import deps


@deps.define
class GitCli:

    @click.command("status")
    def plan(self) -> None:
        """
        Recursive git status.
        """
        asyncio.run(self.git_st())

    async def git_st(self):
        import pathlib

        from zz.services.git import Git

        directory = pathlib.Path(".")
        git = Git()
        result = await git.status_report(directory)
        return result
