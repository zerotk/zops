import click


@click.group(name="tf")
def main():
    pass


@main.command()
def plan():
    """
    Terraform plan with short summary.
    """
    click.echo("""tf.plan""")
    pass


@main.command()
def apply():
    """
    Terraform apply with support to multiple terraform strategies.
    """
    click.echo("""tf.apply""")
    pass
