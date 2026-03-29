from pathlib import Path
from typing import Dict
from typing import List

from zerotk import deps
from zz.services.console import Console
from zz.services.filesystem import FileSystem
from zz.services.template_engine import TemplateEngine


@deps.define
class CodegenEngine:

    filesystem = deps.Singleton(FileSystem)
    template_engine = deps.Singleton(TemplateEngine)
    console = deps.Singleton(Console)

    def run(self, directory):
        playbooks = self.filesystem.Path(directory).rglob("*.codegen.yml")
        for i_playbook in playbooks:
            self._apply_codegen(i_playbook)

    def _apply_codegen(self, playbook_filename):

        def _get_dataset_items(datasets: List, dataset_index: int):
            if dataset_index in ("", "."):
                return [(".", datasets.copy())]

            result = datasets[dataset_index].items()

            # Add 'name' attribute to returning datasets.
            for i_name, i_values in result:
                i_values["name"] = i_name

            return result

        def _create_file(filename: Path, contents: Dict, is_executable: bool = False):
            filename.parent.mkdir(parents=True, exist_ok=True)

            # Cleanup EOL in the end of context making sure we have just one EOL.
            contents = contents.replace(" \n", "\n").rstrip("\n") + "\n"

            filename.write_text(contents)
            if is_executable:
              filename.chmod(0o755)

        def _expand_filename(filename: str, variables):
            return self.template_engine.run(filename, variables)

        def _get_template_contents(template_dir: Path, template_filename: Path, variables):
            return (template_dir / template_filename).read_text()

        template_dir = playbook_filename.parent / "templates"

        spec = self.filesystem.read_yaml(playbook_filename)
        templates = spec["zops.codegen"]["templates"]
        datasets = spec["zops.codegen"]["datasets"]

        for i_template in templates:
            dataset_index = i_template.get("dataset", "")
            filenames = i_template["filenames"]
            variables_default = {}
            for j_name, j_variables in _get_dataset_items(datasets, dataset_index):
                if j_name == "__default__":
                    self.console.title(f"{dataset_index}::{j_name} Loading default variables values.")
                    variables_default = j_variables
                if j_name.startswith("__") and j_name.endswith("__"):
                    self.console.title(f"{dataset_index}::{j_name} SKIPPPED")
                    continue
                self.console.title(f"{dataset_index}::{j_name}")
                for k_template_filename in filenames:
                    template_filename = (template_dir / k_template_filename)
                    template_contents = template_filename.read_text()
                    is_executable = template_filename.stat().st_mode & 0o111
                    variables_apply = variables_default.copy()
                    variables_apply.update(j_variables)
                    target_filename = playbook_filename.parent.parent / self.filesystem.Path(
                        _expand_filename(str(k_template_filename), variables_apply)
                    )
                    self.console.item(str(target_filename))
                    _create_file(
                        target_filename,
                        self.template_engine.run(
                            template_contents,
                            variables_apply,
                            alt_expansion=template_filename.suffix in (".yml", ".yaml")
                        ),
                        is_executable=is_executable
                    )
