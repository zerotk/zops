import asyncio

import click

from zerotk import deps
from zz.services.console import Console
from zz.services.subprocess import SubProcess


@deps.define
class TerraformCli:

    console = deps.Singleton(Console)
    subprocess = deps.Singleton(SubProcess)

    @click.command("plan")
    @click.argument("deployments", nargs=-1)
    @click.option("--skip-init", is_flag=True)
    @click.option("--skip-plan", is_flag=True)
    @click.option("--verbose", is_flag=True)
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
        asyncio.run(self._tf_plan(deployments, skip_init, skip_plan, verbose))

    async def _tf_plan(self, deployments, skip_init, skip_plan, verbose):
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
        
        for i_log in self.subprocess.execution_logs:
            if i_log.is_error():
                console.title(f"{i_log.cmd_line} (retcode: {i_log.retcode})")
                # console._print(i_log.output)

    @click.command("apply")
    def apply(self):
        """
        Terraform apply with support to multiple terraform strategies.
        """
        click.echo("""tf.apply""")
        pass


# main = click.Group(name="tf")
# main.add_command(TerraformCommands.as_click_command("plan"))
# main.add_command(TerraformCommands.as_click_command("apply"))
