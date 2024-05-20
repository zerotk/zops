import click


@click.group(name="codegen")
def main():
    pass


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
@click.argument("directory", type=click.Path())
def apply_anatomy(directory):
    """
    Generate code based on Anatomy templates.
    """
    from zz.anatomy import AnatomyEngine

    codegen = AnatomyEngine()
    codegen.run(directory)
