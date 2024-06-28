import asyncio

import click

from zerotk import deps
from zz.services.console import Console
from zz.services.subprocess import SubProcess
from zz.services.terraform import Terraform


@deps.define
class TerraformCli:

    console = deps.Singleton(Console)
    subprocess = deps.Singleton(SubProcess)
    terraform = deps.Singleton(Terraform)

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
        result = await self.terraform.generate_reports(
            deployments, skip_init=skip_init, skip_plan=skip_plan
        )

        self.console.title("Terraform changes report")
        for i in result:
            self.terraform.print_report(i)

        for i_log in self.subprocess.execution_logs:
            if i_log.is_error():
                self.console.title(f"{i_log.cmd_line} (retcode: {i_log.retcode})")
                # console._print(i_log.output)

    @click.command("apply")
    @click.argument("deployments", nargs=-1)
    @click.option("--skip-init", is_flag=True)
    @click.option("--verbose", is_flag=True)
    def apply(
        self,
        deployments: list[str],
        skip_init: bool,
        verbose: bool,
    ) -> None:
        """
        Terraform apply with support to multiple terraform strategies.
        """
        asyncio.run(self._tf_apply(deployments, skip_init=skip_init, verbose=verbose))

    async def _tf_apply(self, deployments, skip_init, verbose):
        await self.terraform.apply(deployments, skip_init=skip_init)

        for i_log in self.subprocess.execution_logs:
            if i_log.is_error():
                self.console.title(f"{i_log.cmd_line} (retcode: {i_log.retcode})")
                # console._print(i_log.output)


# main = click.Group(name="tf")
# main.add_command(TerraformCommands.as_click_command("plan"))
# main.add_command(TerraformCommands.as_click_command("apply"))
