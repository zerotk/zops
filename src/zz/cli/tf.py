import click


@click.group(name="tf")
def main():
    pass


@main.command(name="plan")
@click.argument("deployments", nargs=-1)
# @click.option("--workspace", default=None)
@click.option("--skip-init", is_flag=True)
@click.option("--skip-plan", is_flag=True)
@click.option("--verbose", is_flag=True)
def plan(
    deployments: list[str],
    # workspace: str,
    skip_init: bool,
    skip_plan: bool,
    verbose: bool
) -> None:
    """
    Terraform plan with short summary.
    """
    from zz.services.console import Console
    from zz.terraform import TerraformPlanner
    import pathlib
    import contextlib


    def split_deployment(deployment_seed):
        import re
        DEPLOYMENT_SEED_RE = re.compile(
            "^(?:(?P<workdir>[\w/]+)\:)?(?P<deployment>[\w/-]+)?(?:\|(?P<workspace>[\w]+))?$"
        )
        workdir, deployment, workspace = DEPLOYMENT_SEED_RE.match(deployment_seed).groups()
        if workspace is None:
            workspace = deployment
        workdir = pathlib.Path.cwd() if workdir is None else pathlib.Path(workdir)
        return workdir, deployment, workspace

    planner = TerraformPlanner(
        console=Console(verbose_level=1 if verbose else 0),
    )
    for i_seed in deployments:
        workdir, deployment, workspace = split_deployment(i_seed)
        planner.run(workdir, deployment, workspace=workspace, init=not skip_init, plan=not skip_plan)


@main.command()
def apply():
    """
    Terraform apply with support to multiple terraform strategies.
    """
    click.echo("""tf.apply""")
    pass
