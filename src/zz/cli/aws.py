import click

from zerotk import deps
from zz.services.aws_provider import Cloud, AwsLocal, AwsProvider
from zz.services.cmd_wrapper import CommandWrapper
from zz.services.console import Console


@deps.define
class AwsCli:

    console = deps.Singleton(Console)
    aws_local = deps.Singleton(AwsLocal)
    cloud_factory = deps.Factory(Cloud)
    cmd_wrapper = deps.Singleton(CommandWrapper)

    @click.command("c")
    def cloud(self):
        """
        List registered cloud accounts profiles.
        """
        clouds = self.aws_local.list_clouds()
        result = self.cmd_wrapper.items(clouds, header="Available cloud profiles")
        return result

    @click.command("d")
    def deployments(self):
        """
        List registered deployments.
        """
        self.console._print(
            """
            deployment   aws_profile  newrelic   sentry
            * tier1-dev    mi-dev       518442355  tier1-dev
            * tier1-stage  mi-stage     544578180  moto-stage
            * tier1-prod   tier1        516056459  t1-moto-prod
            """
        )

    @click.command("ec2.list")
    @click.argument("profile")
    @click.argument("region", default="ca-central-1")
    def ec2_list(self, profile, region):
        """
        List ec2 instances.
        """
        self.deps.shared["Singleton"][("AwsProvider", "aws")] = AwsProvider(profile=profile, region=region)
        cloud = self.cloud_factory(profile)
        for i in cloud.list_ec2_instances():
            self.console.item(i.instance_id)

    @click.command("ec2.shell")
    def ec2_shell(self):
        """
        Shell into an ec2 instance.
        """
        self.console.todo("ec2.shell")

    @click.command("ec2.start")
    def ec2_start(self):
        """
        Starts a stopped ec2 instance.
        """
        self.console.todo("ec2.start")

    @click.command("ec2.stop")
    def ec2_stop(self):
        """
        Stops a running ec2 instance.
        """
        self.console.todo("ec2.stop")

    @click.command("params.list")
    def params_list(self):
        """
        List SSM Parameters.
        """
        pass

    @click.command("params.get")
    def params_get(self):
        """
        Get the value of one or more SSM parameters.
        """
        pass

    @click.command("params.set")
    def params_set(self):
        """
        Sets the value of one or more SSM Parameters.
        """
        pass

    @click.command("ami.list")
    def ami_list(self):
        """
        List AMI images.
        """
        pass

    @click.command("ami.deregister")
    def ami_build(self):
        """
        Deregister (delete) an AMI image.
        """
        pass

    @click.command("asg.list")
    def asg_list(self):
        """
        List ASGs (auto scaling groups).
        """
        pass

    @click.command("asg.update")
    def asg_update(self):
        """
        Updates an ASG (auto scaling group).
        """
        pass
