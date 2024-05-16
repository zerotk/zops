import click


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
@click.argument("directory", type=click.Path())
def apply_codegen(directory):
    """
    Generate code based on local .codegen templates and configuration files.
    """
    from zz.codegen import CodegenEngine

    codegen = CodegenEngine()
    codegen.run(directory)


@main.command("apply-anatomy")
@click.argument("directories", nargs=-1)
@click.option("--features-file", default=None, envvar="ZOPS_ANATOMY_FEATURES")
@click.option("--templates-dir", default=None, envvar="ZOPS_ANATOMY_TEMPLATES")
@click.option("--playbook-file", default=None)
@click.option("--recursive", "-r", is_flag=True)
@click.pass_context
def apply_anatomy(
    ctx, directories, features_file, templates_dir, playbook_file, recursive
):
    """
    Generate code based on Anatomy templates.
    """
    from zz.services.console import Console
    from zz.services.filesystem import FileSystem

    filesystem = FileSystem.singleton()
    console = Console.singleton()

    playbooks = []
    for i_directory in directories:
        playbooks += filesystem.Path(i_directory).rglob("anatomy-playbook.yml")

    for i_playbook in playbooks:
        _apply_anatomy(i_playbook, templates_dir, console=console)


def _apply_anatomy(playbook_filename, templates_dir, console):
    from zz.anatomy.layers.feature import AnatomyFeatureRegistry
    from zz.anatomy.layers.playbook import AnatomyPlaybook

    console.info(f"Playbook {playbook_filename}")

    features_filename = _find_features(playbook_filename)
    templates_dir = templates_dir or features_filename.parent / "templates"
    console.info(f"Features {features_filename}")

    AnatomyFeatureRegistry.clear()
    AnatomyFeatureRegistry.register_from_file(features_filename, templates_dir)
    AnatomyPlaybook.from_file(playbook_filename).apply(playbook_filename.parent)


def _find_features(playbook_filename):
    import pathlib

    from zerotk.path import find_up
    from zz.services.console import Console

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
