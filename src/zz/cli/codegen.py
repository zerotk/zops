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
@click.argument("directories", nargs=-1)
@click.option("--features-file", default=None, envvar="ZOPS_ANATOMY_FEATURES")
@click.option("--templates-dir", default=None, envvar="ZOPS_ANATOMY_TEMPLATES")
@click.option("--playbook-file", default=None)
@click.option("--project-name", default=None)
@click.option("--recursive", "-r", is_flag=True)
@click.pass_context
def apply_anatomy(ctx, directories, features_file, templates_dir, playbook_file, project_name, recursive):
    """
    Generate code based on Anatomy templates.
    """
    from zz.anatomy.layers.feature import AnatomyFeatureRegistry
    from zz.anatomy.layers.playbook import AnatomyPlaybook
    import os
    from zz.services.console import Console

    for i_directory in directories:
        playbook_filename = _find_playbook(i_directory, project_name)
        Console.info(f"Playbook {playbook_filename}")

        features_filename = _find_features(playbook_filename)
        templates_dir = templates_dir or features_filename.parent / "templates"
        Console.info(f"Features {features_filename}")

        AnatomyFeatureRegistry.clear()
        AnatomyFeatureRegistry.register_from_file(features_filename, templates_dir)
        AnatomyPlaybook.from_file(playbook_filename).apply(i_directory)


def _find_playbook(directory, project_name):
    import pathlib
    from zerotk.path import find_up

    result = pathlib.Path(directory).absolute() / "anatomy-playbook.yml"
    if not result.exists():
        raise RuntimeError(f"FATAL: Can't find playbook: {project_filename}")

    return result


def _find_features(playbook_filename):
    from zerotk.path import find_up
    from zz.services.console import Console
    import pathlib

    SEARCH_FILENAMES = [
        pathlib.Path("anatomy-features/anatomy-features.yml"),
        pathlib.Path("anatomy-features.yml"),
    ]

    for i_filename in SEARCH_FILENAMES:
        result = find_up(i_filename, playbook_filename.parent)
        if result is not None:
            break

    if result is None:
        Console.error("Can't find features file: anatomy-features.yml.")
        raise SystemError(1)

    return pathlib.Path(result)


def _register_features(filename, templates_dir):
    from zz.anatomy.layers.feature import AnatomyFeatureRegistry

    AnatomyFeatureRegistry.clear()
    AnatomyFeatureRegistry.register_from_file(filename, templates_dir)
