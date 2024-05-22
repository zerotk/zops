import pathlib

import attrs

from zz.services.console import Console
from zz.services.filesystem import FileSystem
from zerotk.text import dedent


@attrs.define
class TerraformPlanner:

    filesystem: attrs.field = FileSystem.singleton()
    console: attrs.field = Console.singleton()

    ACTION_MAP = {
        "update": "~",
        "create": "+",
        "delete": "-",
        "replace": "!",
    }

    def run(
        self,
        workdir: pathlib.Path,
        deployment: str,
        workspace: str = None,
        init: bool = True,
        plan: bool = True,
    ):
        import contextlib

        with contextlib.chdir(workdir):
            self.console.title(f"{deployment}", verbosity=0)

            tfplan_bin = self.filesystem.Path(f".terraform/{deployment}.tfplan.bin")
            tfplan_json = self.filesystem.Path(f"./.terraform/{deployment}.tfplan.json")
            var_file = f"tfvars/{deployment}.tfvars"
            if workspace is None:
                workspace = deployment

            self.console.title("Initializing terraform", indent=1, verbosity=1)
            if init:
                if self.filesystem.Path("./bin/init").exists():
                    self.console.item("Using ./bin/init", indent=2, verbosity=1)
                    self.filesystem.run("./bin/init")
                else:
                    self.console.item("Using terraform", indent=2, verbosity=1)
                    self.filesystem.run("terraform init")
            else:
                self.console.item(
                    "Skipping (Use --init option to run init)", indent=2, verbosity=1
                )

            config = TerraformConfig(workdir)

            self.console.title(
                f"Generating terraform plan binary file: {tfplan_bin}", indent=1, verbosity=1
            )
            if plan:
                if self.filesystem.Path("./bin/plan").exists():
                    self.console.title("* Using ./bin/plan", indent=1, verbosity=1)
                    cmd_line = f"./bin/plan {deployment} -out {tfplan_bin}"
                else:
                    self.console.item(
                        f"Selecting workspace {workspace}", indent=2, verbosity=1
                    )
                    self.filesystem.run(f"terraform workspace select {workspace}")

                    cmd_line = f"terraform plan -out {tfplan_bin}"
                    if FileSystem.Path(var_file).exists():
                        self.console.item(
                            f"Found terraform variables file: {var_file}",
                            indent=2,
                            verbosity=1,
                        )
                        cmd_line += f" -var-file {var_file}"
                self.filesystem.run(cmd_line)

                self.console.title(
                    f"Generating terraform plan json file: {tfplan_json}", indent=1, verbosity=1
                )
                completed_process = self.filesystem.run(
                    f"terraform show -json {tfplan_bin}"
                )
                tfplan_json.write_text(completed_process.stdout.decode("UTF-8"))
            else:
                self.console.item(
                    f"Skipping (Use --plan option to run plan)", indent=2, verbosity=1
                )

            self.console.title(
                f"Reading terraform plan json file: {tfplan_json}", indent=1, verbosity=1
            )
            changes = self.filesystem.read_json(tfplan_json).resource_changes
            output = {}
            for i_change in changes:
                actions = [self.ACTION_MAP.get(i, i) for i in i_change.change.actions]
                actions = "/".join(actions)
                if actions in ("no-op", "read"):
                    continue
                filename = config._get_filename(workdir, i_change.address)
                output.setdefault(filename, []).append(f"{actions} {i_change.address}")

            self.console.title("Terraform plan summary:", indent=1, verbosity=1)
            if output:
                for i_filename, i_changes in sorted(output.items()):
                    self.console.secho(i_filename)
                    for j_change in i_changes:
                        format, comment = self._get_change_format(i_filename, j_change)
                        if comment:
                            comment = f"  # {comment}"
                        self.console.secho(f"  {j_change}{comment}", **format)
            else:
                self.console.secho(f"(no changes)")

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
            r = self.filesystem.run(f"terraform-config-inspect --json {directory}")
            terraform_configuration = r.stdout.decode("UTF-8")
            terraform_configuration = self.filesystem.read_json_string(
                terraform_configuration
            )

            if r.returncode != 0:
                diag = terraform_configuration.diagnostics[0]
                if diag.summary == "Failed to read module directory":
                    click.echo(f"WARNING: {diag.summary}: {directory}")
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
