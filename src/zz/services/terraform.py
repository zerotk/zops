import asyncio
import pathlib

import addict
import typing
import re

from zerotk import deps

from .caches import Caches
from .console import Console
from .filesystem import FileSystem
from .subprocess import SubProcess
from .text import Text


@deps.define
class TerraformConfig:
    """
    Interface to terraform configuration data.
    """

    caches = deps.Singleton(Caches)
    filesystem = deps.Singleton(FileSystem)
    subprocess = deps.Singleton(SubProcess)
    text = deps.Singleton(Text)

    workdir: FileSystem.Path = deps.field(default=".")

    async def _modules(self, workdir, module):
        cache_key, result = self.caches.get("TerraforConfig._modules", workdir, module)

        if result is None:
            result = {}

            modules_filename = workdir / ".terraform/modules/modules.json"
            raw_modules = self.filesystem.read_json(modules_filename)
            raw = {}
            for i_module in raw_modules.Modules:
                try:
                    raw[i_module.Key] = await self._terraform_config_inspect(
                        workdir / i_module.Dir
                    )
                except Exception as e:
                    raise RuntimeError(
                        f"While loading terraform configuration for module: {modules_filename}"
                    ) from e
            result = raw.get(module, (None, None))
            self.caches.set("TerraforConfig._modules", cache_key, result)

        return result

    async def _resources_map(self, workdir, root_filename=None, module="", prefix=""):
        cache_key, result = self.caches.get(
            "TerraformConfig._resources_map", root_filename, module, prefix
        )

        if result is None:
            result = {}

            resources, modules = await self._modules(workdir, module)

            if resources is None:
                return {}

            for i_resource, i_filename in resources.items():
                result[f"{prefix}{i_resource}"] = root_filename or i_filename

            for i_module in modules:
                if module == "":
                    full_module = i_module
                else:
                    full_module = f"{module}.{i_module}"
                r = await self._resources_map(
                    workdir,
                    root_filename or modules[i_module],
                    full_module,
                    f"{prefix}module.{i_module}.",
                )
                result.update(r)

            self.caches.set("TerraformConfig._resources_map", cache_key, result)

        return result

    async def _get_filename(self, workdir, addr: str) -> str:
        """
        Return the filename associated with the given addr.
        """
        import re

        # Remove everything between brackets
        addr = re.sub(r"\[.*?\]", "", addr)
        result = await self._resources_map(workdir)
        return self.filesystem.Path(result.get(addr, "?"))

    async def _terraform_config_inspect(self, directory):
        """
        Return a map between resources names and their filenames in the given project.
        """
        directory = self.filesystem.Path(directory).resolve()
        cache_key, result = self.caches.get(
            "TerraformConfig._terraform_config_inspect", directory
        )

        if result is None:
            r = await self.subprocess.run_async(
                f"terraform-config-inspect --json {directory}", cwd=directory
            )
            terraform_configuration = self.filesystem.read_json_string(r.output)

            if r.retcode != 0:
                diag = terraform_configuration.diagnostics[0]
                if diag.summary == "Failed to read module directory":
                    self.console.warning(f"{diag.summary}: {directory}")
                    return
                else:
                    raise RuntimeError(
                        self.text.dedent(
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


@deps.define
class Terraform:

    filesystem = deps.Singleton(FileSystem)
    console = deps.Singleton(Console)
    subprocess = deps.Singleton(SubProcess)
    config_factory = deps.Factory(TerraformConfig)

    _semaphores: list = deps.field(default_factory=list)

    ACTION_MAP = {
        "update": "~",
        "create": "+",
        "delete": "-",
        "replace": "!",
    }

    class ExecutionError(RuntimeError):
        pass

    # =============================================================================================== run (sync)

    def run(self, cmd, cwd: str, *args) -> None:
        """
        Runs terraform plan for the given infrastructure.

        Uses shell scripts found on terraform/infrastructure/bin directory.
        """
        self.subprocess.call(["bin/init"], cwd=str(cwd))
        self.subprocess.call([f"bin/{cmd}", *args], cwd=str(cwd))

    # =============================================================================================== Apply

    async def apply(self, deployments_seeds, skip_init=False):
        deployments, workdirs = self._list_deployments(deployments_seeds)

        result = []

        # Initialize each workdir only once
        self.console.title("Initializing (terraform init)")
        init_functions = [
            self._run_init(i_workdir, skip_init=skip_init) for i_workdir in workdirs
        ]
        await asyncio.gather(*init_functions)
        self.console.clear_blocks()

        # First stop. If any of the initialization fails we stop the process.
        if not self._check_continue():
            return result

        # Run the report for all deployments
        self.console.title("Applying...")

        titles = {}
        for i_workdir, i_deployment, _workspace in deployments:
            title = i_deployment
            if not i_deployment.startswith(i_workdir.name):
                title = f"{i_workdir.name}:{title}"
            self.console.create_block(title, "...")
            titles[i_deployment] = title

        self._semaphores = {i: asyncio.Semaphore(1) for i in workdirs}
        functions = [
            self._apply_deployment(
                i_workdir,
                i_deployment,
                i_workspace,
                title=titles[i_deployment],
                semaphore=self._semaphores[i_workdir],
            )
            for i_workdir, i_deployment, i_workspace in deployments
        ]
        result = await asyncio.gather(*functions)

        # Second and last stop. Check for any errors in the external executions.
        self._check_continue()

        return result

    async def _apply_deployment(
        self,
        workdir: pathlib.Path,
        deployment: str,
        workspace: str,
        title: str,
        semaphore: asyncio.Semaphore = None,
    ):
        workspace = workspace or deployment
        result = addict.Dict(
            deployment=deployment,
            workspace=workspace,
            workdir=workdir,
            changes=[],
        )
        try:
            self.console.update_block(title, f"waiting for {workdir}")
            async with semaphore:
                self.console.update_block(title, "apply")
                await self._run_apply(workdir, deployment, workspace)
        except self.ExecutionError as e:
            self.console.update_block(
                title, f"[red]error: (NOT HERE DEBUG)[/red] {e.__class__.__name__}"
            )
        except Exception as e:
            self.console.update_block(
                title, f"[red]error: (NOT HERE DEBUG)[/red] {e.__class__.__name__}"
            )
            raise
        return result

    async def _run_apply(
        self,
        workdir: pathlib.Path,
        deployment: str,
        workspace: str,
    ) -> None:
        var_file = f"tfvars/{deployment}.tfvars"

        cmd_line = "terraform apply --auto-approve"
        if (workdir / var_file).exists():
            cmd_line += f" -var-file {var_file}"
        select_workspace = workspace or deployment

        if select_workspace:
            r = await self.subprocess.run_async(
                f"terraform workspace select {select_workspace}", cwd=workdir
            )
            if r.is_error():
                raise self.ExecutionError(r)

        r = await self.subprocess.run_async(cmd_line, cwd=workdir)
        if r.is_error():
            raise self.ExecutionError(r)

        return

    # =============================================================================================== Plan (report)

    async def generate_reports(
        self, deployments_seeds, skip_init=False, skip_plan=False
    ):
        deployments, workdirs = self._list_deployments(deployments_seeds)

        result = []

        # Initialize each workdir only once
        self.console.title("Initializing (terraform init)")
        init_functions = [
            self._run_init(i_workdir, skip_init=skip_init) for i_workdir in workdirs
        ]
        await asyncio.gather(*init_functions)
        self.console.clear_blocks()

        # First stop. If any of the initialization fails we stop the process.
        if not self._check_continue():
            return result

        # Run the report for all deployments
        self.console.title("Generating reports (terraform plan + report generation)")

        titles = {}
        for i_workdir, i_deployment, _workspace in deployments:
            title = i_deployment
            if not i_deployment.startswith(i_workdir.name):
                title = f"{i_workdir.name}:{title}"
            self.console.create_block(title, "...")
            titles[i_deployment] = title

        self._workdir_semaphores = {i: asyncio.Semaphore(1) for i in workdirs}
        self._plan_semaphore = asyncio.Semaphore(1)
        self._report_semaphore = asyncio.Semaphore(1)
        generate_report_functions = [
            self._generate_report(
                i_workdir,
                i_deployment,
                i_workspace,
                title=titles[i_deployment],
                skip_plan=skip_plan,
                workdir_semaphore=self._workdir_semaphores[i_workdir],
                plan_semaphore=self._plan_semaphore,
                report_semaphore=self._report_semaphore,
            )
            for i_workdir, i_deployment, i_workspace in deployments
        ]
        result = await asyncio.gather(*generate_report_functions)

        # Second and last stop. Check for any errors in the external executions.
        self._check_continue()

        return result

    async def _generate_report(
        self,
        workdir: pathlib.Path,
        deployment: str,
        workspace: str,
        title: str,
        skip_plan: bool = False,
        workdir_semaphore: asyncio.Semaphore = None,
        plan_semaphore: asyncio.Semaphore = None,
        report_semaphore: asyncio.Semaphore = None,
    ):
        workspace = workspace or deployment
        result = addict.Dict(
            deployment=deployment,
            workspace=workspace,
            workdir=workdir,
            changes=[],
            errors=[],
        )
        try:
            self.console.update_block(title, f"waiting for {workdir}")
            async with workdir_semaphore, plan_semaphore:
                self.console.update_block(title, "plan")
                tf_plan = await self._run_plan(
                    workdir, deployment, workspace, skip_plan
                )

            async with report_semaphore:
                self.console.update_block(title, "report")
                result = addict.Dict(
                    deployment=deployment,
                    workspace=workspace,
                    workdir=workdir,
                    changes=await self._generate_changes(workdir, tf_plan),
                    errors=[],
                )
            count = len(result["changes"])
            if count == 0:
                self.console.update_block(title, "[green]no changes[/green]")
            else:
                self.console.update_block(title, f"[yellow]{count} change(s)[/yellow]")
        except self.ExecutionError as e:
            self.console.update_block(
                title, f"[red]error (ExecutionError):[/red] {e}"
            )
            result.errors.append(e)
        except Exception as e:
            self.console.update_block(
                title, f"[red]error (Exception):[/red] {e.__class__.__name__}"
            )
            result.errors.append(e)
        return result

    async def _run_plan(
        self,
        workdir: pathlib.Path,
        deployment: str,
        workspace: str,
        skip_plan: bool = False,
    ) -> str:
        bin_plan = "bin/plan"
        tfplan_bin = f".terraform/{deployment}.tfplan"
        tfplan_json = f".terraform/{deployment}.tfplan.json"
        var_file = f"tfvars/{deployment}.tfvars"

        # Select the executable
        if (workdir / bin_plan).exists():
            cmd_line = f"{bin_plan} {deployment} -out {tfplan_bin}"
            select_workspace = False
        else:
            cmd_line = f"terraform plan -out {tfplan_bin}"
            if (workdir / var_file).exists():
                cmd_line += f" -var-file {var_file}"
            select_workspace = workspace or deployment

        if not skip_plan:
            if select_workspace:
                r = await self.subprocess.run_async(
                    f"terraform workspace select {select_workspace}", cwd=workdir
                )
                if r.is_error():
                    raise self.ExecutionError(r)

            r = await self.subprocess.run_async(cmd_line, cwd=workdir)
            if r.is_error():
                if "Error acquiring the state lock" in r.error:
                    match = re.search(r"ID:\s+([a-f0-9-]+)", r.error)
                    lock_id = match.group(1) if match else "unknown"
                    r.retcode = 0
                    raise self.ExecutionError(f"Locked: {lock_id}")
                raise self.ExecutionError(r)

            r = await self.subprocess.run_async(
                f"terraform show -json {tfplan_bin}", cwd=workdir
            )
            if r.is_error():
                raise self.ExecutionError(r)

            # Cleanup output to remove eventual error messages.
            # Eg.:
            #   2025-03-04T12:59:40.762Z [ERROR] provider: error encountered while scanning stdout: error="read |0: file already closed"
            try:
                output = "\n".join([i for i in r.output.splitlines() if i.startswith("{")])
                (workdir / tfplan_json).write_text(output)
            except Exception as e:
                raise self.ExecutionError(str(e))

        return self.filesystem.read_json(workdir / tfplan_json)

    async def _generate_changes(self, workdir, tf_plan):
        config = self.config_factory(workdir=workdir)
        result = {}
        for i_change in tf_plan.resource_changes:
            actions = [self.ACTION_MAP.get(i, i) for i in i_change.change.actions]
            actions = "/".join(actions)
            if actions in ("no-op", "read"):
                continue
            filename = await config._get_filename(workdir, i_change.address)
            try:
                filename = filename.relative_to(workdir.absolute())
            except ValueError:
                pass  # Ignore if the path is not relative.
            result.setdefault(filename, []).append(f"{actions} {i_change.address}")

        return result

    def print_report(self, report):
        changes = report["changes"]
        if not changes:
            return
        self.console.title(report.deployment, indent=1)
        for i_filename, i_changes in sorted(changes.items()):
            self.console.title(i_filename.name, indent=2)
            for j_change in i_changes:
                color, comment = self._get_change_format(i_filename, j_change)
                if comment:
                    comment = f"  # {comment}"
                self.console.item(comment, indent=3, prefix=j_change, color=color)

    def _get_change_format(self, filename: str, change: str):
        r_format = "white"
        r_comment = ""
        if change.startswith("+/-") or change.startswith("-/+"):
            r_format = "white"
        elif change.startswith("-"):
            r_format = "red"
        elif change.startswith("+"):
            r_format = "green"
        elif change.startswith("~"):
            r_format = "green"
        return r_format, r_comment

    # =============================================================================================== Init

    async def _run_init(self, workdir: pathlib.Path, skip_init: bool = False) -> bool:
        self.console.create_block(workdir, "init")

        if skip_init:
            self.console.update_block(workdir, "init: [yellow]skip[/yellow]")
            return True

        bin_init = "bin/init"

        if (workdir / bin_init).exists():
            cmd_line = bin_init
        else:
            cmd_line = "terraform init -no-color"

        r = await self.subprocess.run_async(cmd_line, cwd=workdir)
        if r.is_error():
            self.console.update_block(workdir, "init: [red]error[/red]")
        else:
            self.console.update_block(workdir, "init: [green]done[/green]")

        return not r.is_error()

    # =============================================================================================== Deployments

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

    # =============================================================================================== Workflow

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
                f"Execution failed for '{i_result.cmd_line}' (retcode: {i_result.retcode})\n{i_result.error}",
            )
        return result


#     async def _fake_run(self):
#         import random
#
#         sleep_time = 3 + int(4 * random.random())
#         await asyncio.sleep(sleep_time)
#         return sleep_time
