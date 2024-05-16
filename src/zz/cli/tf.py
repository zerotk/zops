import click


@click.group(name="tf")
def main():
    pass


@main.command(name="plan")
@click.argument("deployment")
@click.option("--workspace", default=None)
@click.option("--skip-init", is_flag=True)
@click.option("--skip-plan", is_flag=True)
@click.option("--verbose", is_flag=True)
def plan(
    deployment: str, workspace: str, skip_init: bool, skip_plan: bool, verbose: bool
) -> None:
    """
    Terraform plan with short summary.
    """
    from zz.services.console import Console
    from zz.terraform.terraform import TerraformPlanner

    planner = TerraformPlanner(
        console=Console(verbose_level=1 if verbose else 0),
    )
    planner.run(deployment, workspace=workspace, init=not skip_init, plan=not skip_plan)


@main.command()
def apply():
    """
    Terraform apply with support to multiple terraform strategies.
    """
    click.echo("""tf.apply""")
    pass
