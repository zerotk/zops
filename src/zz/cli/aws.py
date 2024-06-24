import click
from zerotk import deps
from zz.services.console import Console
from zz.services.aws_provider import AwsProvider
from zz.services.aws import Aws
from zz.services.cmd_wrapper import CommandWrapper


@deps.define
class Cloud:

    aws = deps.Singleton(Aws)

    profile_name: str

    def ec2_list(self):
        pass


@deps.define
class AwsCli:

    console = deps.Singleton(Console)
    aws_provider = deps.Factory(AwsProvider)
    aws = deps.Singleton(Aws)
    cloud_factory = deps.Factory(Cloud)
    cmd_wrapper = deps.Singleton(CommandWrapper)

    @deps.Command("c")
    def cloud(self):
        """
        List registered cloud accounts profiles.
        """
        from rich.pretty import pprint

        profiles = self.aws.list_profiles()
        result = [self.cloud_factory(i) for i in profiles]
        result = self.cmd_wrapper.items(
            result,
            header="Available cloud profiles"
        )
        pprint(self.appliances.tree.items)
        return result

        # from zz.services.aws_provider import AwsProvider
        import boto3
        import botocore

        for i, i_profile in enumerate(boto3.session.Session().available_profiles):
            try:
                aws = self.aws_provider(profile=i_profile, region=None)
                s = aws.session
                identity = s.client("sts").get_caller_identity()
                print(identity)
                account_id = identity["Account"]
            except botocore.exceptions.NoCredentialsError:
                account_id = "?"
            self.console.item(f"{i_profile} {account_id}")
            # TODO: Remove after tests
            if i > 3:
                break

    @deps.Command("d")
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

    @deps.Command("ec2.list")
    @click.argument("seed")
    def ec2_list(self, seed):
        """
        List ec2 instances.
        """
        cloud = self.cloud_factory(seed)
        cloud.list_ec2_instances()
        self.console.todo("ec2.list")

    @deps.Command("ec2.shell")
    def ec2_shell(self):
        """
        Shell into an ec2 instance.
        """
        self.console.todo("ec2.shell")

    @deps.Command("ec2.start")
    def ec2_start(self):
        """
        Starts a stopped ec2 instance.
        """
        self.console.todo("ec2.start")

    @deps.Command("ec2.stop")
    def ec2_stop(self):
        """
        Stops a running ec2 instance.
        """
        self.console.todo("ec2.stop")

    @deps.Command("params.list")
    def params_list(self):
        """
        List SSM Parameters.
        """
        pass

    @deps.Command("params.get")
    def params_get(self):
        """
        Get the value of one or more SSM parameters.
        """
        pass

    @deps.Command("params.set")
    def params_set(self):
        """
        Sets the value of one or more SSM Parameters.
        """
        pass

    @deps.Command("ami.list")
    def ami_list(self):
        """
        List AMI images.
        """
        pass

    @deps.Command("ami.deregister")
    def ami_build(self):
        """
        Deregister (delete) an AMI image.
        """
        pass

    @deps.Command("asg.list")
    def asg_list(self):
        """
        List ASGs (auto scaling groups).
        """
        pass

    @deps.Command("asg.update")
    def asg_update(self):
        """
        Updates an ASG (auto scaling group).
        """
        pass
