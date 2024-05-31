import pathlib

import attrs

from zz.services.console import Console
from zz.services.filesystem import FileSystem
from zerotk.text import dedent
import asyncio


@attrs.define
class TerraformPlanner:

    filesystem: attrs.field = FileSystem.singleton()
    console: attrs.field = Console.singleton()
    _semaphores: list[asyncio.Semaphore] = []

    ACTION_MAP = {
        "update": "~",
        "create": "+",
        "delete": "-",
        "replace": "!",
    }

    async def run_all(self, deployments_seeds):
        deployments, workdirs = self._list_deployments(deployments_seeds)

        # Initialize each workdir only once
        await asyncio.gather(*[
            self._run_init(i_workdir)
            for i_workdir in workdirs
        ])
        self.console.clear_blocks()

        # Run the report for all deployments
        self._semaphores = {
            i: asyncio.Semaphore(1)
            for i in workdirs
        }
        run_list = [
            self.run(
                i_workdir,
                i_deployment,
                i_workspace,
                semaphore=self._semaphores[i_workdir],
            )
            for i_workdir, i_deployment, i_workspace in deployments
        ]
        result = await asyncio.gather(*run_list)
        return result

    async def run(
        self,
        workdir: pathlib.Path,
        deployment: str,
        workspace: str = None,
        semaphore: asyncio.Semaphore = None,
    ):
        if workspace is None:
            workspace = deployment

        title = deployment
        if not deployment.startswith(workdir.name):
            title = f"{workdir.name}:{deployment}"
        self.console.create_block(title, title)

        # IDEAS:
        # - Use semaphore only for the tasks that cannot be executed at the same time,
        #   namely, the terraform calls
        self.console.update_block(title, f"waiting for {workdir}")
        async with semaphore:           
            self.console.update_block(title, "plan")
            tf_plan = await self._run_plan(workdir, deployment, workspace)
        self.console.update_block(title, "report")
        result = await self._generate_report(workdir, tf_plan)
        self.console.update_block(title, "finished")
        return result

    async def _fake_run(self):
        import random
        sleep_time = 3 + int(4 * random.random())
        await asyncio.sleep(sleep_time)
        return sleep_time

    async def _run_init(self, workdir: pathlib.Path) -> None:
        self.console.create_block(workdir, "init")

        bin_init = "bin/init"

        if (workdir / bin_init).exists():
            cmd_line = bin_init
        else:
            cmd_line = "terraform init -no-color"
        retcode, output = await self.filesystem.run_async(cmd_line, cwd=workdir)

        # TODO: Store output for future. Show in case of errors.
        self.console.update_block(workdir, f"init: done")
        return output

    async def _run_plan(self, workdir: pathlib.Path, deployment: str, workspace: str) -> None:
        bin_plan = "bin/plan"
        tfplan_bin = workdir / f".terraform/{deployment}.tfplan.bin"
        tfplan_json = workdir / f".terraform/{deployment}.tfplan.json"

        if (workdir / bin_plan).exists():
            cmd_line = f"{bin_plan} {deployment} -out {tfplan_bin}"
        else:
            _retcode, _stdout = await self.filesystem.run_async(
                f"terraform workspace select {workspace}", cwd=workdir
            )
            cmd_line = f"terraform plan -out {tfplan_bin}"
            if FileSystem.Path(var_file).exists():
                cmd_line += f" -var-file {var_file}"
        _retcode, _stdout = await self.filesystem.run_async(
            cmd_line, cwd=workdir
        )
        _retcode, stdout = await self.filesystem.run_async(
            f"terraform show -json {tfplan_bin}", cwd=workdir
        )
        tfplan_json.write_text(stdout)
        return self.filesystem.read_json(tfplan_json)

    async def _generate_report(self, workdir, tf_plan):
        config = TerraformConfig(workdir)
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
            self.console.secho(f"(no changes)")

    @classmethod
    def split_deployment(cls, deployment_seed: str) -> tuple[pathlib.Path, str, str]:
        import re

        DEPLOYMENT_SEED_RE = re.compile(
            "^(?:(?P<workdir>[\w/]+)\:)?(?P<deployment>[\w/-]+)?(?:\|(?P<workspace>[\w]+))?$"
        )
        workdir, deployment, workspace = DEPLOYMENT_SEED_RE.match(deployment_seed).groups()
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


class Cached:

    def __init__(self, name):
        self._name = name
        self._results = {}

    def get(self, *args):
        cache_key = tuple(args)
        result = self._results.get(cache_key, None)
        # if result is None:
        #     hitmiss = "MISS"
        # else:
        #     hitmiss = "hit"
        # print(f"{self._name}( {cache_key} )")
        return cache_key, result

    def set(self, cache_key, value):
        self._results[cache_key] = value


@attrs.define
class TerraformConfig:
    """
    Interface to terraform configuration data.
    """

    _resources_map_cache = Cached("_resources_map")
    _modules_cache = Cached("_modules")
    _terraform_config_inspect_cache = Cached("_terraform_config_inspect")

    workdir: FileSystem.Path
    filesystem: attrs.field = FileSystem.singleton()

    def _modules(self, workdir, module):
        cache_key, result = self._modules_cache.get(workdir, module)

        if result is None:
            result = {}

            modules_filename = ".terraform/modules/modules.json"
            raw_modules = self.filesystem.read_json(modules_filename)
            raw = {}
            for i_module in raw_modules.Modules:
                raw[i_module.Key] = self._terraform_config_inspect(i_module.Dir)
            result = raw.get(module, (None, None))
            self._modules_cache.set(cache_key, result)

        return result


    def _resources_map(self, workdir, root_filename=None, module="", prefix=""):
        cache_key, result = self._resources_map_cache.get(root_filename, module, prefix)

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

            self._resources_map_cache.set(cache_key, result)

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
        cache_key, result = self._terraform_config_inspect_cache.get(directory)

        if result is None:
            retcode, terraform_configuration = self.filesystem.run_async(f"terraform-config-inspect --json {directory}", cwd=workdir)
            terraform_configuration = self.filesystem.read_json_string(terraform_configuration)

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
            for i_module_name, i_details in terraform_configuration.module_calls.items():
                modules_map[i_module_name] = i_details.pos.filename

            result = (resources_map, modules_map)

            self._terraform_config_inspect_cache.set(cache_key, result)

        return result
