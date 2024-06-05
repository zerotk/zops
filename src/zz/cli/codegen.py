import click


@click.command(name="codegen")
@click.argument("directory", type=click.Path(), default=".")
def main(directory):
    from zz.anatomy import AnatomyEngine
    from zz.codegen import CodegenEngine
    from zerotk.wiring import Appliances

    appliances = Appliances()

    codegen = AnatomyEngine(appliances=appliances)
    codegen.run(directory)

    codegen = CodegenEngine(appliances=appliances)
    codegen.run(directory)
