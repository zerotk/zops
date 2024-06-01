import pathlib
from typing import Dict
from typing import Iterable

import attrs

from zerotk.wiring import Appliance


@attrs.define
class FileSystem(Appliance):
    """
    Central point of access to file system to make tests easier.
    """

    Path = pathlib.Path

    def iterdir(self, path: Path) -> Iterable:
        return path.iterdir()

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
