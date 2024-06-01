import asyncio
import pathlib

import attrs

from zerotk.text import dedent
from zerotk.wiring import Appliance
from zerotk.wiring import Dependency
from zerotk.wiring import Requirements
from zz.services.caches import Caches
from zz.services.console import Console
from zz.services.filesystem import FileSystem
from zz.services.subprocess import Subprocess


@attrs.define
class TerraformPlanner(Appliance):

    injector = Requirements(
        filesystem=Dependency(FileSystem),
        console=Dependency(Console),
        subprocess=Dependency(Subprocess),
    )

    _semaphores: list[asyncio.Semaphore] = []

    ACTION_MAP = {
        "update": "~",
        "create": "+",
        "delete": "-",
        "replace": "!",
    }

    class ExecutionError(RuntimeError):
        pass

    async def generate_reports(self, deployments_seeds):
        deployments, workdirs = self._list_deployments(deployments_seeds)

        result = []

        # Initialize each workdir only once
        self.console.title("Initializing (terraform init)")
        init_functions = [self._run_init(i_workdir) for i_workdir in workdirs]
        await asyncio.gather(*init_functions)
        self.console.clear_blocks()

        # First stop. If any of the initialization fails we stop the process.
        if not self._check_continue():
            return result

        # Run the report for all deployments
        self.console.title("Generating reports (terraform plan + report generation)")
        self._semaphores = {i: asyncio.Semaphore(1) for i in workdirs}
        generate_report_functions = [
            self.generate_report(
                i_workdir,
                i_deployment,
                i_workspace,
                semaphore=self._semaphores[i_workdir],
            )
            for i_workdir, i_deployment, i_workspace in deployments
        ]
        result = await asyncio.gather(*generate_report_functions)

        # Second and last stop. Check for any errors in the external executions.
        self._check_continue()

        return result

    async def generate_report(
        self,
        workdir: pathlib.Path,
        deployment: str,
        workspace: str = None,
        semaphore: asyncio.Semaphore = None,
    ):
        workspace = workspace or deployment

        title = deployment
        if not deployment.startswith(workdir.name):
            title = f"{workdir.name}:{deployment}"

        result = {}
        try:
            self.console.create_block(title, f"waiting for {workdir}")
            async with semaphore:
                self.console.update_block(title, "plan")
                tf_plan = await self._run_plan(workdir, deployment, workspace)

            self.console.update_block(title, "report")
            result = await self._generate_report(workdir, tf_plan)

            self.console.update_block(title, "[green]finished[/green]")
        except self.ExecutionError:
            self.console.update_block(title, "[red]error[/red]")

        return result

    async def _run_init(self, workdir: pathlib.Path) -> bool:
        self.console.create_block(workdir, "init")

        bin_init = "bin/init"

        if (workdir / bin_init).exists():
            cmd_line = bin_init
        else:
            cmd_line = "terraform init -no-color"

        r = await self.subprocess.run_async(cmd_line, cwd=workdir)
        if r.is_error():
            self.console.update_block(workdir, "[red]init[/red]")
        else:
            self.console.update_block(workdir, "[green]init[/green]")

        return not r.is_error()

    async def _run_plan(
        self, workdir: pathlib.Path, deployment: str, workspace: str
    ) -> None:
        bin_plan = "bin/plan"
        tfplan_bin = f".terraform/{deployment}.tfplan.bin"
        tfplan_json = f".terraform/{deployment}.tfplan.json"
        var_file = f"tfvars/{deployment}.tfvars"

        if (workdir / bin_plan).exists():

            cmd_line = f"{bin_plan} {deployment} -out {tfplan_bin}"
        else:
            r = await self.subprocess.run_async(
                f"terraform workspace select {workspace}", cwd=workdir
            )
            if r.is_error():
                raise self.ExecutionError(r)
            cmd_line = f"terraform plan -out {tfplan_bin}"
            if (workdir / var_file).exists():
                cmd_line += f" -var-file {var_file}"

        r = await self.subprocess.run_async(cmd_line, cwd=workdir)
        if r.is_error():
            raise self.ExecutionError(r)

        r = await self.subprocess.run_async(
            f"terraform show -json {tfplan_bin}", cwd=workdir
        )
        if r.is_error():
            raise self.ExecutionError(r)

        (workdir / tfplan_json).write_text(r.output)

        return self.filesystem.read_json(workdir / tfplan_json)

    async def _generate_report(self, workdir, tf_plan):
        config = TerraformConfig(appliances=self.appliances, workdir=workdir)
        result = {}
        for i_change in tf_plan.resource_changes:
            actions = [self.ACTION_MAP.get(i, i) for i in i_change.change.actions]
            actions = "/".join(actions)
            if actions in ("no-op", "read"):
                continue
            filename = config._get_filename(workdir, i_change.address)
            result.setdefault(filename, []).append(f"{actions} {i_change.address}")

        return result

    def _get_change_format(self, filename: str, change: str):
        r_format = dict(fg="white")
        r_comment = ""
        if (
            change.startswith("-")
            or change.startswith("+/-")
            or change.startswith("-/+")
        ):
            r_format = dict(fg="red")
        elif change.startswith("+"):
            r_format = dict(fg="green")
        return r_format, r_comment

    def print_report(self, changes_report):
        self.console.title("Terraform plan summary:", indent=1, verbosity=1)
        if changes_report:
            for i_filename, i_changes in sorted(changes_report.items()):
                self.console.secho(i_filename)
                for j_change in i_changes:
                    format, comment = self._get_change_format(i_filename, j_change)
                    if comment:
                        comment = f"  # {comment}"
                    self.console.secho(f"  {j_change}{comment}", **format)
        else:
            self.console.secho("(no changes)")

    @classmethod
    def split_deployment(cls, deployment_seed: str) -> tuple[pathlib.Path, str, str]:
        import re

        DEPLOYMENT_SEED_RE = re.compile(
            r"^(?:(?P<workdir>[\w/]+)\:)?(?P<deployment>[\w/-]+)?(?:\|(?P<workspace>[\w]+))?$"
        )
        workdir, deployment, workspace = DEPLOYMENT_SEED_RE.match(
            deployment_seed
        ).groups()
        if workspace is None:
            workspace = deployment
        workdir = pathlib.Path.cwd() if workdir is None else pathlib.Path(workdir)
        return workdir, deployment, workspace

    @classmethod
    def _list_deployments(cls, deployments_seeds):
        r_deployments = []
        r_workdirs = set()
        for i_seed in deployments_seeds:
            workdir, deployment, workspace = cls.split_deployment(i_seed)
            r_workdirs.add(workdir)
            r_deployments.append((workdir, deployment, workspace))
        return r_deployments, r_workdirs

    def _check_continue(self):
        """
        Check the subprocess service for execution errors printing errors messages if any error
        happened. Returns True if there was no errors.
        """
        result = True
        for i_result in self.subprocess.execution_logs:
            if not i_result.is_error():
                continue
            result = False
            self.console.error(
                f"Execution failed for '{i_result.cmd_line}' (retcode: {i_result.retcode})",
                i_result.output,
            )
        return result

    async def _fake_run(self):
        import random

        sleep_time = 3 + int(4 * random.random())
        await asyncio.sleep(sleep_time)
        return sleep_time


@attrs.define
class TerraformConfig(Appliance):
    """
    Interface to terraform configuration data.
    """

    injector = Requirements(
        caches=Dependency(Caches),
        filesystem=Dependency(FileSystem),
    )

    workdir: FileSystem.Path

    def _modules(self, workdir, module):
        cache_key, result = self.caches.get("TerraforConfig._modules", workdir, module)

        if result is None:
            result = {}

            modules_filename = ".terraform/modules/modules.json"
            raw_modules = self.filesystem.read_json(modules_filename)
            raw = {}
            for i_module in raw_modules.Modules:
                raw[i_module.Key] = self._terraform_config_inspect(i_module.Dir)
            result = raw.get(module, (None, None))
            self.caches.set("TerraforConfig._modules", cache_key, result)

        return result

    def _resources_map(self, workdir, root_filename=None, module="", prefix=""):
        cache_key, result = self.caches.get(
            "TerraformConfig._resources_map", root_filename, module, prefix
        )

        if result is None:
            result = {}

            resources, modules = self._modules(workdir, module)

            if resources is None:
                return {}

            for i_resource, i_filename in resources.items():
                result[f"{prefix}{i_resource}"] = root_filename or i_filename

            for i_module in modules:
                if module == "":
                    full_module = i_module
                else:
                    full_module = f"{module}.{i_module}"
                r = self._resources_map(
                    workdir,
                    root_filename or modules[i_module],
                    full_module,
                    f"{prefix}module.{i_module}.",
                )
                result.update(r)

            self.caches.set("TerraformConfig._resources_map", cache_key, result)

        return result

    def _get_filename(self, workdir, addr: str) -> str:
        """
        Return the filename associated with the given addr.
        """
        import re

        # Remove everything between brackets
        addr = re.sub(r"\[.*?\]", "", addr)
        return self._resources_map(workdir).get(addr, "?")

    def _terraform_config_inspect(self, directory):
        """
        Return a map between resources names and their filenames in the given project.
        """
        directory = self.filesystem.Path(directory).resolve()
        cache_key, result = self.caches.get(
            "TerraformConfig._terraform_config_inspect", directory
        )

        if result is None:
            retcode, terraform_configuration = self.subprocess.run_async(
                f"terraform-config-inspect --json {directory}", cwd=directory
            )
            terraform_configuration = self.filesystem.read_json_string(
                terraform_configuration
            )

            if retcode != 0:
                diag = terraform_configuration.diagnostics[0]
                if diag.summary == "Failed to read module directory":
                    self.console.secho(f"WARNING: {diag.summary}: {directory}")
                    return
                else:
                    raise RuntimeError(
                        dedent(
                            f"""
                            Call to terreaform-config-inspect failed with message:
                            {diag.summary}
                            {diag.detail}
                            """
                        )
                    )

            resources_map = {}
            for i_name, i_details in terraform_configuration.managed_resources.items():
                resources_map[i_name] = i_details.pos.filename

            modules_map = {}
            for (
                i_module_name,
                i_details,
            ) in terraform_configuration.module_calls.items():
                modules_map[i_module_name] = i_details.pos.filename

            result = (resources_map, modules_map)

            self.caches.set(
                "TerraformConfig._terraform_config_inspect", cache_key, result
            )

        return result
