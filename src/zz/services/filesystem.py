import functools
import pathlib
from typing import Dict
from typing import Iterable


class FileSystem:
    """
    Central point of access to file system to make tests easier.
    """

    @classmethod
    @functools.cache
    def singleton(cls) -> "FileSystem":
        return cls()

    Path = pathlib.Path

    def iterdir(self, path: Path) -> Iterable:
        return path.iterdir()

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

    async def run_async(self, cmd_line: str, cwd: str = None) -> tuple[int ,str]:
        import asyncio

        proc = await asyncio.create_subprocess_shell(
            cmd_line,
            stderr=asyncio.subprocess.STDOUT,
            stdout=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, _ = await proc.communicate()
        return proc.returncode, stdout.decode("UTF-8")


    @classmethod
    def read_hcl(cls, filename: Path) -> Dict:
        import hcl2

        if not filename.is_file():
            raise RuntimeError(f"Can't find file: {filename}.")
        with filename.open("r") as file:
            return hcl2.load(file)

    @classmethod
    def read_yaml(cls, filename: Path) -> Dict:
        import yaml

        with open(filename, "r") as iss:
            return yaml.safe_load(iss)

    @classmethod
    def read_json(cls, filename: Path) -> Dict:
        import json

        from addict import Dict as AttrDict

        with open(filename, "r") as iss:
            return json.load(iss, object_hook=AttrDict)

    @classmethod
    def read_json_string(cls, contents: str) -> Dict:
        import json

        from addict import Dict as AttrDict

        return json.loads(contents, object_hook=AttrDict)
