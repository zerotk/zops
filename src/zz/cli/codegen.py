import click


@click.group(name="codegen")
def main():
    pass


@main.command("apply-codegen")
def apply_codegen():
    """
    Generate code based on local .codegen templates and configuration files.
    """
    pass


@main.command("apply-anatomy")
def apply_anatomy():
    """
    Generate code based on Anatomy templates.
    """
    pass
