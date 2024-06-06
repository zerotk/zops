from .subprocess import SubProcess
from zerotk.appliance import Appliance


@Appliance.define
class Terraform(Appliance):
    """
    Terraform singleton.
    """

    __requirements__ = Appliance.Requirements(
        subprocess = SubProcess,
    )

    def run(self, cmd, cwd: str, *args) -> None:
        """
        Runs terraform plan for the given infrastructure.

        Uses shell scripts found on terraform/infrastructure/bin directory.
        """
        self.subprocess.call(["bin/init"], cwd=str(cwd))
        self.subprocess.call([f"bin/{cmd}", *args], cwd=str(cwd))
