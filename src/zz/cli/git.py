import asyncio

import click

from zerotk.wiring import Appliances


@click.group(name="git")
def main():
    pass


@main.command(name="st")
def plan() -> None:
    """
    Recursive git status.
    """
    asyncio.run(git_st())


async def git_st():
    from zz.services.git import Git
    import pathlib

    directory = pathlib.Path(".")
    git = Git()
    result = await git.status_report(directory)
