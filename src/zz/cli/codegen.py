import click
from typing import List, Dict
from pathlib import Path


@click.group(name="codegen")
@click.pass_context
def main(ctx):
    from zz.services.filesystem import FileSystem
    from zz.services.template_engine import TemplateEngine

    class Services:
        filesystem = FileSystem.singleton()
        template_engine = TemplateEngine.singleton()

    ctx.obj = Services()


@main.command("apply-codegen")
@click.argument("filename", type=click.Path())
@click.pass_obj
def apply_codegen(services, filename):
    """
    Generate code based on local .codegen templates and configuration files.
    """
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

    template_dir = services.filesystem.Path(filename).parent / "templates"

    spec = services.filesystem.read_yaml(filename)
    templates = spec["zops.codegen"]["templates"]
    datasets = spec["zops.codegen"]["datasets"]

    for i_template in templates:
        dataset_index = i_template.get('dataset', "")
        filenames = i_template['filenames']
        for j_name, j_values in _get_dataset_items(datasets, dataset_index):
            click.echo(f"{dataset_index}::{j_name}")
            for k_filename in filenames:
                filename = services.filesystem.Path(k_filename.replace("__name__", j_name))
                click.echo(f"  * {filename}")
                contents = services.template_engine.expand(
                    open(f"{template_dir}/{k_filename}", "r").read(),
                    j_values
                )
                _create_file(filename, contents)


@main.command("apply-anatomy")
def apply_anatomy():
    """
    Generate code based on Anatomy templates.
    """
    pass
