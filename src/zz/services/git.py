import functools
from zerotk.wiring import Appliance, Requirements, Dependency
from .filesystem import FileSystem
from .console import Console
from .subprocess import Subprocess
import attrs
import asyncio


@attrs.define
class Git(Appliance):
    """
    Git
    """

    injector = Requirements(
        console = Dependency(Console),
        filesystem = Dependency(FileSystem),
        subprocess = Dependency(Subprocess)
    )

    async def status_report(self, directory: FileSystem.Path = FileSystem.Path.cwd()) -> None:

        def is_enabled(path: FileSystem.Path):
            i_part = path
            while str(i_part) not in ["/", ".", "", None]:
                if i_part.name[0] in [".", "_"]:
                    return False
                i_part = i_part.parent
            return True

        directories = directory.rglob(".git")
        directories = [i.parent for i in directories]
        directories = [i for i in directories if is_enabled(i)]
        directories = sorted(directories)

        self.console.title(f"Git status for {directory}")

        concurrency = 8
        semaphore = asyncio.Semaphore(concurrency)
        functions = [self.git_st(i, semaphore) for i in directories]

        await asyncio.gather(*functions)
        self.console.clear_blocks()


    async def git_st(self, directory, semaphore):
        self.console.create_block(directory, f"[white]{directory}[/white]: ...")
        async with semaphore:
            self.console.update_block(directory, f"[white]{directory}[/white]: sync")

            r = await self.subprocess.run_async("hub sync", cwd=directory)
            status = r.output.split("\n")[0]
            if r.retcode != 0:
                self.console.update_block(directory, f"[white]{directory}[/white]: [red]sync[/red]")
                return

            self.console.update_block(directory, f"[white]{directory}[/white]: status")

            r = await self.subprocess.run_async("git status -b -s", cwd=directory)
            if r.retcode != 0:
                self.console.update_block(directory, f"[white]{directory}[/white]: [red]status[/red]")

            status = r.output.split("\n")[0]
            self.console.update_block(directory, f"[white]{directory}[/white]: {status}")
