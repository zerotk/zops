import click


@click.group(name="tf")
def main():
    pass


@main.command(name="plan")
@click.argument("deployment")
@click.option("--verbose", is_flag=True)
def plan(deployment: str, verbose: bool) -> None:
    """
    Terraform plan with short summary.
    """
    from zz.terraform.terraform import TerraformPlanner

    planner = TerraformPlanner(verbose=verbose)
    planner.run(deployment)


@main.command()
def apply():
    """
    Terraform apply with support to multiple terraform strategies.
    """
    click.echo("""tf.apply""")
    pass
