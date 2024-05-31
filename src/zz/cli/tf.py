import click
import asyncio


@click.group(name="tf")
def main():
    pass


@main.command(name="plan")
@click.argument("deployments", nargs=-1)
@click.option("--skip-init", is_flag=True)
@click.option("--skip-plan", is_flag=True)
@click.option("--verbose", is_flag=True)
def plan(
    deployments: list[str],
    skip_init: bool,
    skip_plan: bool,
    verbose: bool
) -> None:
    """
    Terraform plan with short summary.

    Accepts multiple parameters, each parameter with the format:

    [<workdir>:]<deployment>[|<workspace>]

    Eg.:
      tf plan t3can-stage apps/t3can:t3can-stage apps/t3can:t3can-stage|stage
    """
    asyncio.run(tf_plan(deployments, skip_init, skip_plan, verbose))


async def tf_plan(deployments, skip_init, skip_plan, verbose):

    from zz.services.console import Console
    from zz.terraform import TerraformPlanner
    import pathlib

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

    result = []
    workdirs = set()
    for i_seed in deployments:
        workdir, deployment, workspace = split_deployment(i_seed)
        workdirs.add(workdir)
        result.append((workdir, deployment, workspace))

    semaphores = {
        i: asyncio.Semaphore(1)
        for i in workdirs
    }
    functions = [
        planner_run(
            semaphores[i_workdir],
            planner,
            i_workdir,
            i_deployment,
            i_workspace
        )
        for i_workdir, i_deployment, i_workspace in result
    ]
    # tasks = [
    #     asyncio.create_task(
    #         planner_run(
    #             semaphores[i_workdir],
    #             planner,
    #             i_workdir,
    #             i_deployment,
    #             i_workspace
    #         )
    #         for i_workdir, i_deployment, i_workspace in result
    #     )
    # ]
    r = await asyncio.gather(*functions)

    for i in r:
        print("***", i)
    # for i_task in asyncio.as_completed(tasks):
    #     r = await i_task
    #     print(f"Details of task x {r}")


async def planner_run(semaphore, planner, workdir, deployment, workspace):

    async with semaphore:
        return await planner.run(workdir, deployment, workspace)


@main.command()
def apply():
    """
    Terraform apply with support to multiple terraform strategies.
    """
    click.echo("""tf.apply""")
    pass
