import asyncio

import click

from zerotk.wiring import Appliances


@click.group(name="tf")
def main():
    pass


@main.command(name="plan")
@click.argument("deployments", nargs=-1)
@click.option("--skip-init", is_flag=True)
@click.option("--skip-plan", is_flag=True)
@click.option("--verbose", is_flag=True)
def plan(
    deployments: list[str], skip_init: bool, skip_plan: bool, verbose: bool
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

    console = Console(verbose_level=1 if verbose else 0)
    appliances = Appliances(consoel=console)

    # NOTE: We want to use the same instance of the planner to use and reuse the caches.
    planner = TerraformPlanner(appliances=appliances)
    result = await planner.generate_reports(deployments)

    console.title("Terraform changes report")
    for i in result:
        planner.print_report(i)
    # for i_task in asyncio.as_completed(tasks):
    #     r = await i_task
    #     print(f"Details of task x {r}")


@main.command()
def apply():
    """
    Terraform apply with support to multiple terraform strategies.
    """
    click.echo("""tf.apply""")
    pass
