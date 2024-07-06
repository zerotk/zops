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

        def _create_file(filename: Path, contents: Dict):
            filename.parent.mkdir(parents=True, exist_ok=True)

            # Cleanup EOL in the end of context making sure we have just one EOL.
            contents = contents.replace(" \n", "\n").rstrip("\n") + "\n"

            filename.write_text(contents)

        template_dir = playbook_filename.parent / "templates"

        spec = self.filesystem.read_yaml(playbook_filename)
        templates = spec["zops.codegen"]["templates"]
        datasets = spec["zops.codegen"]["datasets"]

        for i_template in templates:
            dataset_index = i_template.get("dataset", "")
            filenames = i_template["filenames"]
            for j_name, j_values in _get_dataset_items(datasets, dataset_index):
                self.console.title(f"{dataset_index}::{j_name}")
                for k_filename in filenames:
                    filename = self.filesystem.Path(
                        k_filename.replace("__name__", j_name)
                    )
                    self.console.item(str(filename))
                    contents = self.template_engine.run(
                        open(f"{template_dir}/{k_filename}", "r").read(), j_values
                    )
                    _create_file(filename, contents)
