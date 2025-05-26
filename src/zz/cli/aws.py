import datetime

import click
from addict import Dict as AttrDict

from zerotk import deps
from zz.services.aws_provider import AwsLocal
from zz.services.aws_provider import Cloud
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

    @classmethod
    def _getattr(cls, obj, attr, default=None):
        result = obj
        for i in attr.split("."):
            result = getattr(result, i)
            if i == "tags":
                result = AttrDict({i["Key"]: i["Value"] for i in result})
            elif isinstance(result, dict):
                result = AttrDict(result)
            elif isinstance(result, datetime.datetime):
                result = result.strftime("%Y-%m-%d %H:%M")
            elif result is None:
                return default
        return str(result)

    @classmethod
    def _asdict(cls, item, attrs):
        return {i: cls._getattr(item, i, "?") for i in attrs}

    @click.command("ec2.list")
    @click.argument("profile")
    @click.argument("region", default="ca-central-1")
    def ec2_list(self, profile, region):
        """
        List ec2 instances.

        ec2.list mi-tier3(profile)
        ec2.list tier3-prod-app(asg)
        ec2.list tier3(project)
        ec2.list tier3-stage(deployment)

        * The input is a seed that can be a aws_profile, asg, project, deployment
        * From the seed define wich aws_accounts, regions and filters we have to use:
            * aws-profile: easy, just list all instances
            * asg: obtain aws_profile+region and a list of instances that are part of the ASG
            * project: obtain aws_profile+region and a prefix (eg.: tier3) or tag filter
            * deployment: obtain aws_profile+region and the prefix (eg.: tier3-prod) or tag filters.
        """
        cloud = self.cloud_factory(profile, region)
        instances = cloud.list_ec2_instances()
        items = [
            self._asdict(
                i, ["launch_time", "id", "tags.Name", "state.Name", "image.id"]
            )
            for i in instances
        ]
        self.cmd_wrapper.items(items)

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
    @click.argument("profile")
    @click.argument("region", default="ca-central-1")
    def ami_list(self, profile, region):
        """
        List AMI images.
        """
        cloud = self.cloud_factory(profile, region)
        items = cloud.list_ami_images()
        items = [self._asdict(i, ["creation_date", "image_id", "name"]) for i in items]
        self.cmd_wrapper.items(items)

    @click.command("ami.deregister")
    def ami_build(self):
        """
        Deregister (delete) an AMI image.
        """
        pass

    @click.command("asg.list")
    @click.argument("profile")
    @click.argument("region", default="ca-central-1")
    def asg_list(self, profile, region):
        """
        List ASGs (auto scaling groups).
        """
        cloud = self.cloud_factory(profile, region)
        items = cloud.list_auto_scaling_groups()
        items = [
            self._asdict(i, ["AutoScalingGroupName"])
            for i in items
        ]
        self.cmd_wrapper.items(items)

    @click.command("asg.update")
    def asg_update(self):
        """
        Updates an ASG (auto scaling group).
        """
        pass

    @click.command("rds.list_snapshots")
    @click.argument("profile")
    @click.argument("region", default="ca-central-1")
    def rds_list_snapshots(self, profile, region):
        """
        List rds/aurora snapshots.
        """
        cloud = self.cloud_factory(profile, region)
        items = cloud.list_rds_snapshots()
        items = [
            self._asdict(i, ["DBSnapshotIdentifier", "SnapshotCreateTime", "Status"])
            for i in items
        ]
        self.cmd_wrapper.items(items)

    @click.command("secrets.list")
    @click.argument("profile")
    @click.argument("region", default="ca-central-1")
    def secrets_list(self, profile, region):
        """
        List rds/aurora snapshots.
        """
        cloud = self.cloud_factory(profile, region)
        secrets = cloud.list_secrets()
        items = [
            self._asdict(i, ["Name", "Description", "DeletedDate"]) for i in secrets
        ]
        self.cmd_wrapper.items(items)
