import attrs
import pathlib
from zz.services.filesystem import FileSystem
from zz.services.console import Console


@attrs.define
class TerraformPlanner:

    workdir:FileSystem.Path = FileSystem.Path.cwd()
    filesystem: attrs.field = FileSystem.singleton()
    console: attrs.field = Console.singleton()

    ACTION_MAP = {
        "update": "~",
        "create": "+",
        "delete": "-",
        "replace": "!",
    }

    def run(self, deployment:str, workspace:str = None, init:bool=True, plan:bool=True):
        tfplan_bin = self.filesystem.Path(f"./.terraform/{deployment}.tfplan.bin")
        tfplan_json = self.filesystem.Path(f"./.terraform/{deployment}.tfplan.json")
        var_file = f"tfvars/{deployment}.tfvars"
        if workspace is None:
            workspace = deployment

        self.console.title("Initializing terraform", verbosity=1)
        if init:
            if self.filesystem.Path("./bin/init").exists():
                self.console.item(f"Using ./bin/init", indent=1, verbosity=1)
                self.filesystem.run("./bin/init")
            else:
                self.console.item(f"Using terraform", indent=1, verbosity=1)
                self.filesystem.run("terraform init")
        else:
            self.console.item(f"Skipping (Use --init option to run init)", indent=1, verbosity=1)


        config = TerraformConfig(self.workdir)

        self.console.title(f"Generating terraform plan binary file: {tfplan_json}", verbosity=1)
        if plan:
            if self.filesystem.Path("./bin/plan").exists():
                self.console.title(f"* Using ./bin/plan", verbosity=1)
                cmd_line =f"./bin/plan {deployment} -out {tfplan_bin}"
            else:
                self.console.item(f"Selecting workspace {workspace}", indent=1, verbosity=1)
                self.filesystem.run(f"terraform workspace select {workspace}")

                cmd_line =f"terraform plan -out {tfplan_bin}"
                if FileSystem.Path(var_file).exists():
                    self.console.item(f"Found terraform variables file: {var_file}", indent=1, verbosity=1)
                    cmd_line += f" -var-file {var_file}"
            self.filesystem.run(cmd_line)

            self.console.title(f"Generating terraform plan json file: {tfplan_json}", verbosity=1)
            completed_process = self.filesystem.run(f"terraform show -json {tfplan_bin}")
            tfplan_json.write_text(completed_process.stdout.decode("UTF-8"))
        else:
            self.console.item(f"Skipping (Use --plan option to run plan)", indent=1, verbosity=1)

        self.console.title(f"Reading terraform plan json file: {tfplan_json}", verbosity=1)
        changes = self.filesystem.read_json(tfplan_json).resource_changes
        output = {}
        for i_change in changes:
            actions = [self.ACTION_MAP.get(i, i) for i in i_change.change.actions]
            actions = "/".join(actions)
            if actions in ("no-op", "read"):
                continue

            filename = config.get_filename(i_change.address)
            output.setdefault(filename, []).append(f"{actions} {i_change.address}")

        self.console.title("Terraform plan summary:", verbosity=1)
        for i_filename, i_changes in sorted(output.items()):
            self.console.secho(i_filename)
            for j_change in i_changes:
                format, comment = self._get_change_format(i_filename, j_change)
                if comment:
                    comment = f"  # {comment}"
                self.console.secho(f"  {j_change}{comment}", **format)

    def _get_change_format(self, filename: str, change: str):
        r_format = dict(fg="white")
        r_comment = ""
        if change.startswith("-") or change.startswith("+/-") or change.startswith("-/+"):
            r_format = dict(fg="red")
        elif change.startswith("+"):
            r_format = dict(fg="green")
        return r_format, r_comment


@attrs.define
class TerraformConfig:
    """
    Interface to terraform configuration data.
    """

    workdir: FileSystem.Path
    filesystem: attrs.field = FileSystem.singleton()

    def resources_map(self, module="", prefix="", root_filename=None):
        modules_filename = self.workdir / ".terraform/modules/modules.json"
        raw_modules = self.filesystem.read_json(modules_filename)
        raw = {}
        for i_module in raw_modules.Modules:
            raw[i_module.Key] = self._terraform_config_inspect(i_module.Dir)
        resources, modules = raw.get(module, (None, None))

        if resources is None:
            print(f"ERROR: Cant find raw data about module {module}")
            return {}

        result = {}
        for i_resource, i_filename in resources.items():
            result[f"{prefix}{i_resource}"] = root_filename or i_filename

        for i_module in modules:
            if module == "":
                full_module = i_module
            else:
                full_module = f"{module}.{i_module}"
            r = self.resources_map(
                full_module,
                f"{prefix}module.{i_module}.",
                root_filename or modules[i_module],
            )
            result.update(r)

        return result

    def get_filename(self, addr: str) -> str:
        """
        Return the filename associated with the given addr.
        """
        import re

        # Remove everything between brackets
        addr = re.sub(r"\[.*?\]", "", addr)
        return self.resources_map().get(addr, "?")


    def _terraform_config_inspect(self, directory):
        """
        Return a map between resources names and their filenames in the given project.
        """
        r = self.filesystem.run(f"terraform-config-inspect --json {directory}")
        terraform_configuration = r.stdout.decode("UTF-8")
        terraform_configuration = self.filesystem.read_json_string(terraform_configuration)

        if r.returncode != 0:
            diag = terraform_configuration.diagnostics[0]
            if diag.summary == "Failed to read module directory":
                click.echo(f"WARNING: {diag.summary}: {directory}")
                return
            else:
                raise RuntimeError(
                    f"""
Call to terreaform-config-inspect failed with message:
{diag.summary}
{diag.detail}
"""
                )

        resources_map = {}
        for i_name, i_details in terraform_configuration.managed_resources.items():
            resources_map[i_name] = i_details.pos.filename

        modules_map = {}
        for i_module_name, i_details in terraform_configuration.module_calls.items():
            modules_map[i_module_name] = i_details.pos.filename

        return resources_map, modules_map
