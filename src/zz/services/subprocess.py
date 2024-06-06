import pathlib
from zerotk.appliance import Appliance


@Appliance.define
class SubProcess(Appliance):
    """
    Call external commands.
    """

    execution_logs = []

    class Result:

        def __init__(self, cmd_line, retcode, output):
            self.cmd_line = cmd_line
            self.retcode = retcode
            self.output = output

        def is_error(self):
            return self.retcode != 0


    def call(self, *args, **kwargs) -> int:
        import subprocess

        result = subprocess.call(*args, shell=False, **kwargs)
        return result

    def run(self, cmd_line: str):
        import shlex
        import subprocess

        return subprocess.run(
            shlex.split(cmd_line),
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
        )

    async def run_async(self, cmd_line: str, cwd: pathlib.Path = None) -> tuple[int ,str]:
        import asyncio

        proc = await asyncio.create_subprocess_shell(
            cmd_line,
            stderr=asyncio.subprocess.STDOUT,
            stdout=asyncio.subprocess.PIPE,
            cwd=str(cwd),
        )
        stdout, _ = await proc.communicate()
        stdout = stdout.decode("UTF-8")
        result = self.Result(cmd_line=cmd_line, retcode=proc.returncode, output=stdout)
        self.execution_logs.append(result)
        return result
