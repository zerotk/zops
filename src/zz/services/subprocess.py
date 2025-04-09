import pathlib

from zerotk import deps


@deps.define
class SubProcess:
    """
    Call external commands.
    """

    execution_logs = []

    class Result:

        def __init__(self, cmd_line, retcode, output, error):
            self.cmd_line = cmd_line
            self.retcode = retcode
            self.output = output
            self.error = error

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

    async def run_async(
        self, cmd_line: str, cwd: pathlib.Path = None
    ) -> tuple[int, str]:
        import asyncio

        proc = await asyncio.create_subprocess_shell(
            cmd_line,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            cwd=str(cwd),
        )
        (stdout, stderr) = await proc.communicate()
        result = self.Result(
            cmd_line=cmd_line,
            retcode=proc.returncode,
            output=stdout.decode("UTF-8"),
            error=stderr.decode("UTF-8"),
            )
        self.execution_logs.append(result)
        return result
