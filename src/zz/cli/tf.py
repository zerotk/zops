import asyncio

import click

from zerotk.appliance import Appliance, Command
from zerotk.appliance import Appliances
from zz.services.console import Console


@Command.define
class TerraformCli(Command):

    __requirements__ = Command.Requirements(
        console=Console,
    )

    def plan(
        self,
        deployments: list[str],
        skip_init: bool,
        skip_plan: bool,
        verbose: bool,
    ) -> None:
        """
        Terraform plan with short summary.

        Accepts multiple parameters, each parameter with the format:

        [<workdir>:]<deployment>[|<workspace>]

        Eg.:
        tf plan t3can-stage apps/t3can:t3can-stage apps/t3can:t3can-stage|stage
        """
        asyncio.run(self.tf_plan(deployments, skip_init, skip_plan, verbose))

    async def tf_plan(self, deployments, skip_init, skip_plan, verbose):
        from zz.services.console import Console
        from zz.terraform import TerraformPlanner

        console = Console(verbose_level=1 if verbose else 0)
        appliances = Appliances(consoel=console)

        # NOTE: We want to use the same instance of the planner to use and reuse the caches.
        planner = TerraformPlanner(appliances=appliances)
        result = await planner.generate_reports(
            deployments, skip_init=skip_init, skip_plan=skip_plan
        )

        console.title("Terraform changes report")
        for i in result:
            planner.print_report(i)

    def apply(self):
        """
        Terraform apply with support to multiple terraform strategies.
        """
        click.echo("""tf.apply""")
        pass


# main = click.Group(name="tf")
# main.add_command(TerraformCommands.as_click_command("plan"))
# main.add_command(TerraformCommands.as_click_command("apply"))
