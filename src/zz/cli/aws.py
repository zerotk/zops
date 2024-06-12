import click
from zerotk.appliance import Command


@Command.define
class AwsCli(Command):

    @click.command("c")
    def cloud(self):
        """
        List registered cloud accounts profiles.
        """
        # from zz.services.aws_provider import AwsProvider
        import boto3
        import botocore

        for i, i_profile in enumerate(boto3.session.Session().available_profiles):
            try:
                s = boto3.session.Session(profile_name=i_profile)
                identity = s.client("sts").get_caller_identity()
                account_id = identity["Account"]
            except botocore.exceptions.NoCredentialsError:
                account_id = "?"
            print(i_profile, account_id)
            if i > 3:
                break

    @click.command("d")
    def deployments(self):
        """
        List registered deployments.
        """
        click.echo(
            """
    deployment   aws_profile  newrelic   sentry
    * tier1-dev    mi-dev       518442355  tier1-dev
    * tier1-stage  mi-stage     544578180  moto-stage
    * tier1-prod   tier1        516056459  t1-moto-prod
    """
        )
        pass

    @click.command("ec2.list")
    def ec2_list(self):
        """
        List ec2 instances.
        """
        pass

    @click.command("ec2.shell")
    def ec2_shell(self):
        """
        Shell into an ec2 instance.
        """
        pass

    @click.command("ec2.start")
    def ec2_start(self):
        """
        Starts a stopped ec2 instance.
        """
        pass

    @click.command("ec2.stop")
    def ec2_stop(self):
        """
        Stops a running ec2 instance.
        """
        pass

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
