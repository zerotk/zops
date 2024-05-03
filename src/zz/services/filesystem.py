import functools
from pathlib import Path
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

    @classmethod
    def Path(cls, *args, **kwargs):
        return Path(*args, **kwargs)

    def iterdir(self, path: Path) -> Iterable:
        return path.iterdir()

    def call(self, *args, **kwargs) -> int:
        import subprocess

        result = subprocess.call(*args, shell=False, **kwargs)
        return result

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
        with open(filename, 'r') as iss:
            return yaml.safe_load(iss)
