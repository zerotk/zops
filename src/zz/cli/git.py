import asyncio
from zerotk import deps


@deps.define
class GitCli:

    @deps.Command
    def plan() -> None:
        """
        Recursive git status.
        """
        asyncio.run(git_st())


    async def git_st():
        import pathlib

        from zz.services.git import Git

        directory = pathlib.Path(".")
        git = Git()
        result = await git.status_report(directory)
        return result
