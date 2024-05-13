from attrs import define
import pathlib


@define
class TerraformPlanner:

    workdir: pathlib.Path = pathlib.Path.cwd()
    verbose: bool = False

    def run(self, deployment:str, workspace:str = None):
        verbose_level = 1 if self.verbose else 0
        tfplan_bin = f"./.terraform/{deployment}.tfplan.bin"
        tfplan_json = f"./.terraform/{deployment}.tfplan.json"
        var_file = f"tfvars/{deployment}.tfvars"
        if workspace is None:
            workspace = deployment

        self._print_status(verbose_level, "Initializing terraform")
        if pathlib.Path("./bin/init").exists():
            self._print_status(verbose_level, f"* Using ./bin/init")
            self._run_command("./bin/init")
        else:
            self._run_command("terraform init")

        config = TerraformConfig(self.workdir)

        self._print_status(verbose_level, f"Generating terraform plan binary file: {tfplan_json}")
        if os.path.isfile("./bin/plan"):
            self._print_status(verbose_level, f"* Using ./bin/plan")
            cmd_line =f"./bin/plan {deployment} -out {tfplan_bin}"
        else:
            self._print_status(verbose_level, f"* Selecting workspace {workspace}")
            self._run_command(f"terraform workspace select {workspace}")

            cmd_line =f"terraform plan -out {tfplan_bin}"
            if os.path.isfile(var_file):
                self._print_status(verbose_level, f"* Found terraform variables file: {var_file}")
                cmd_line += f" -var-file {var_file}"
        self._run_command(cmd_line)

        self._print_status(verbose_level, f"Generating terraform plan json file: {tfplan_json}")
        completed_process = self._run_command(f"terraform show -json {tfplan_bin}")
        open(tfplan_json, "w").write(completed_process.stdout)

        self._print_status(verbose_level, "Reading terraform plan")
        changes = _read_changes(tfplan_json)
        output = {}
        for i_change in changes:
            actions = [ACTION_MAP.get(i, i) for i in i_change.change.actions]
            actions = "/".join(actions)
            if actions in ("no-op", "read"):
                continue

            filename = config.get_filename(i_change.address)
            output.setdefault(filename, []).append(f"{actions} {i_change.address}")

        self._print_status(verbose_level, "Terraform plan summary:")
        for i_filename, i_changes in sorted(output.items()):
            click.echo(i_filename)
            for j_change in i_changes:
                format, comment = _get_change_format(i_filename, j_change)
                if comment:
                    comment = f"  # {comment}"
                click.secho(f"  {j_change}{comment}", **format)

    def _get_change_format(filename: str, change: str):
        r_format = dict(fg="white")
        r_comment = ""
        if "cloudwatch" in change:
            r_format = dict(fg="green")
        elif change.startswith("-") or change.startswith("+/-"):
            r_format = dict(fg="red")
        elif change.startswith("+ "):
            r_format = dict(fg="yellow", bg="green")
        return r_format, r_comment


    def _load_json(filepath):
        return json.load(open(filepath), object_hook=AttrDict)


    def _read_changes(filename):
        return _load_json(filename).resource_changes


    def _terraform_config_inspect(directory):
        """
        Return a map between resources names and their filenames in the given project.
        """
        r = subprocess.run(
            ["terraform-config-inspect", "--json", directory],
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
        )
        configs = json.loads(r.stdout.decode("UTF-8"), object_hook=AttrDict)

        if r.returncode != 0:
            diag = configs.diagnostics[0]
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
        for i_name, i_details in configs.managed_resources.items():
            resources_map[i_name] = i_details.pos.filename

        modules_map = {}
        for i_module_name, i_details in configs.module_calls.items():
            modules_map[i_module_name] = i_details.pos.filename

        return resources_map, modules_map

    def _print_status(self, verbose_level: int, message: str) -> None:
        import click
        if verbose_level > 0:
            click.echo(click.style(message, fg="blue"))

    def _run_command(self, cmdline) -> None:
        import subprocess

        cmdline = cmdline.split()
        try:
            result = subprocess.run(
                cmdline,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            click.echo(e.stdout)
            raise SystemExit(9)
        return result


class TerraformConfig:
    """
    Interface to terraform configuration data.
    """

    def __init__(self, workdir: str):
        """
        :param workdir: The root directory for the terraform project.
        """
        raw_modules = _load_json(f"{workdir}/.terraform/modules/modules.json")

        self._raw = {}
        for i_module in raw_modules.Modules:
            self._raw[i_module.Key] = _terraform_config_inspect(i_module.Dir)

        self._resources_map = self._get_resources_map("")

    def _get_resources_map(self, module, prefix="", root_filename=None):
        resources, modules = self._raw.get(module, (None, None))

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
            r = self._get_resources_map(
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
        # Remove everything between brackets
        addr = re.sub(r"\[.*?\]", "", addr)
        return self._resources_map.get(addr, "?")
