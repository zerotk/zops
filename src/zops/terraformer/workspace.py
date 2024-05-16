import json
import os
import shutil
import subprocess
import tempfile
from logging import getLogger
from pathlib import Path
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

from terraformer.apply_log import TerraformApplyLog

from .exceptions import TerraformError
from .exceptions import TerraformRuntimeError
from .mixins import ProcessResults
from .mixins import TerraformRun
from .plan import TerraformPlan


logger = getLogger(__name__)


class TerraformWorkspace(TerraformRun):
    env: Dict[str, str]

    def __init__(self, path=None, backend_config_path: Optional[Path] = None) -> None:
        self.backend_config_path = backend_config_path
        self.terraform_path = shutil.which("terraform")
        if not self.terraform_path:
            raise TerraformError("Terraform binary is missing from system.")

        results = subprocess.run(
            ["terraform", "-version", "-json"], stdout=subprocess.PIPE
        )
        if results.returncode != 0:
            raise TerraformRuntimeError("Unable to get terraform version", results)

        version_data = json.loads(results.stdout.decode("utf-8"))
        self.version = version_data["terraform_version"]
        self.is_outdated = version_data["terraform_outdated"]

        if self.is_outdated:
            logger.warning(
                f"Terraform version {self.version} is out of date. Please consider updating!"
            )

        self.platform = version_data["platform"]
        self.provider_selections = version_data["provider_selections"]

        self.cwd = path if path != None else Path(os.getcwd())
        self.env = {}

    def init(self) -> ProcessResults:
        run_command = [self.terraform_path, "init"]
        if self.backend_config_path:
            run_command.append(f"-backend-config={str(self.backend_config_path)}")
        return self._subprocess_run(run_command, raise_exception_on_failure=True)

    def validate(self) -> ProcessResults:
        return self._subprocess_run(
            ["terraform", "validate", "-json"], raise_exception_on_failure=True
        )

    def plan(
        self, error_function=None, output_function=None, output_path=None, destroy=False
    ) -> Tuple[ProcessResults, Union[TerraformPlan, None]]:
        save_plan = True
        if not output_path:
            save_plan = False
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, "terraform.plan")

        command = [
            self.terraform_path,
            "plan",
            "-json",
            "-detailed-exitcode",
            "-input=false",
            f"-out={output_path}",
        ]

        if destroy:
            command.append("-destroy")

        results = self._subprocess_stream(
            command,
            error_function=error_function,
            output_function=output_function,
        )

        if results.returncode != 1:
            results.successful = True
            plan = TerraformPlan(cwd=self.cwd, plan_path=output_path)
        else:
            results.successful = False
            plan = None

        if not save_plan:
            shutil.rmtree(temp_dir)

        return results, plan

    def apply(
        self,
        error_function: Callable | None = None,
        output_function: Callable | None = None,
        auto_approve: bool = False,
        plan_file: str | None = None,
    ) -> Tuple[ProcessResults, TerraformApplyLog]:
        command = [self.terraform_path, "apply", "-json"]

        if plan_file:
            command.append(plan_file)
        if auto_approve:
            command.append("-auto-approve")

        results = self._subprocess_stream(
            command,
            error_function=error_function,
            output_function=output_function,
        )

        apply_log = TerraformApplyLog()
        apply_log.add_lines(results.stdout)

        return results, apply_log

    def destroy(
        self,
        auto_approve: bool = False,
        error_function: Callable | None = None,
        output_function: Callable | None = None,
    ) -> Tuple[ProcessResults, TerraformApplyLog]:
        terraform_command = [self.terraform_path, "destroy", "-json"]
        if auto_approve:
            terraform_command.append("-auto-approve")

        results = self._subprocess_stream(
            terraform_command,
            error_function=error_function,
            output_function=output_function,
        )

        apply_log = TerraformApplyLog()
        apply_log.add_lines(results.stdout)

        return results, apply_log

    def output(self) -> ProcessResults:
        return self._subprocess_run([self.terraform_path, "output", "-json"])

    def get(self, update: bool = False) -> ProcessResults:
        command = [self.terraform_path, "get"]
        if update:
            command.append("-update")
        return self._subprocess_run(command)
