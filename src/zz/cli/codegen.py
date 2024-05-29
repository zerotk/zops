import click


@click.command(name="codegen")
@click.argument("directory", type=click.Path(), default=".")
def main(directory):
    from zz.anatomy import AnatomyEngine
    from zz.codegen import CodegenEngine

    codegen = AnatomyEngine()
    codegen.run(directory)

    codegen = CodegenEngine()
    codegen.run(directory)
