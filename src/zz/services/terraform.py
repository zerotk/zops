import functools

from .filesystem import FileSystem


class Terraform:
    """
    Terraform singleton.
    """

    @classmethod
    @functools.cache
    def singleton(cls) -> "Terraform":
        return cls()

    def run(self, cmd, cwd: str, *args) -> None:
        """
        Runs terraform plan for the given infrastructure.

        Uses shell scripts found on terraform/infrastructure/bin directory.
        """
        fs = FileSystem.singleton()
        fs.call(["bin/init"], cwd=str(cwd))
        fs.call([f"bin/{cmd}", *args], cwd=str(cwd))
