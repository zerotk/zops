import os
from os.path import dirname
from zops import Console

import click


@click.command()
@click.argument("directories", nargs=-1)
@click.option("--features-file", default=None, envvar="ZOPS_ANATOMY_FEATURES")
@click.option("--templates-dir", default=None, envvar="ZOPS_ANATOMY_TEMPLATES")
@click.option("--playbook-file", default=None)
@click.option("--project-name", default=None)
@click.option("--recursive", "-r", is_flag=True)
@click.pass_context
def apply(ctx, directories, features_file, templates_dir, playbook_file, project_name, recursive):
    """
    Apply templates.
    """
    from .layers.playbook import AnatomyPlaybook
    from zerotk.path import find_up

    for i_directory in directories:
        project_name = project_name or os.path.basename(os.path.abspath(i_directory))
        project_playbook_filename = f"anatomy-features/playbooks/{project_name}.yml"
        try:
            project_playbook_filename = find_up(project_playbook_filename, i_directory)
        except FileNotFoundError:
            click.echo(f"CRITICAL: Playbook not found: {project_playbook_filename}")
            continue

        if playbook_file is not None:
            playbook_filenames = [playbook_file]
        elif os.path.exists(project_playbook_filename):
            playbook_filenames = [project_playbook_filename]
        elif recursive:
            directory = os.path.abspath(i_directory)
            playbook_filenames = find_all("anatomy-playbook.yml", directory)
            playbook_filenames = GitIgnored().filter(playbook_filenames)
        else:
            playbook_filenames = [i_directory + "/anatomy-playbook.yml"]

        for i_filename in playbook_filenames:
            features_file = features_file or _find_features_file(dirname(i_filename))
            templates_dir = templates_dir or os.path.join(
                os.path.dirname(features_file), "templates"
            )
            Console.info(f"Apply {i_filename}")
            _register_features(features_file, templates_dir)

            Console.title(i_directory)
            anatomy_playbook = AnatomyPlaybook.from_file(i_filename)
            anatomy_playbook.apply(i_directory)


def _find_features_file(path):
    from zerotk.path import find_up

    SEARCH_FILENAMES = [
        "anatomy-features/anatomy-features.yml",
        "anatomy-features.yml",
    ]

    for i_filename in SEARCH_FILENAMES:
        result = find_up(i_filename, path)
        if result is not None:
            break

    if result is None:
        Console.error("Can't find features file: anatomy-features.yml.")
        raise SystemError(1)

    Console.info("Features filename:", result)
    return result


def _register_features(filename, templates_dir):
    from .layers.feature import AnatomyFeatureRegistry

    AnatomyFeatureRegistry.clear()
    AnatomyFeatureRegistry.register_from_file(filename, templates_dir)
