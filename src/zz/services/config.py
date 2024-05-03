import functools
from pathlib import Path
from typing import Iterable
from typing import Tuple


class Config:
    """
    Global configuration settings.
    """

    ROOT_DIR = Path(__file__).parent.parent.parent.parent
    TERRAFORM_PATH = ROOT_DIR.joinpath("./terraform")
    INFRASTRUCTURE_PATH = TERRAFORM_PATH.joinpath("infrastructure")
    APPLICATIONS_PATH = TERRAFORM_PATH.joinpath("applications")

    @classmethod
    @functools.cache
    def singleton(cls) -> "Config":
        return cls()

    def configurations(self) -> Iterable[Tuple[str, str]]:
        result = []
        for i in ["ROOT_DIR", "TERRAFORM_PATH"]:
            value = getattr(self, i)
            result.append(f"{i}: {value}")
        return result
