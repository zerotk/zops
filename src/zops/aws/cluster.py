import copy
import functools
import os
import subprocess
from operator import attrgetter
from typing import Dict

import boto3
import click

from .image import Image
from .instance import Instance
from .utils import format_date
from .utils import get_resource_attr
from .utils_shell import packer


class Cluster:
    """
    Group all information about a given cluster. All specifics for each cluster
    is defined here. The algorithms are the same for all cluster.
    """

    AWS_OWNERS = []

    clusters = {}

    @classmethod
    def get_cluster(cls, cluster):
        result = cls.clusters.get(cluster)
        if result is None:
            raise click.ClickException(f"Invalid cluster name: '{cluster}'.")
        return result

    @classmethod
    def get_cluster_env(cls, cluster_env):
        cluster_name, env = cluster_env.split("-", 1)
        result = Cluster.clusters_arg(cluster_name)
        result = Cluster.get_cluster(result)
        return result, env

    def __init__(
        self,
        name,
        profile,
        regions,
        project=None,
        psql_version=10,
        python_version="3.6",
        requires_name="requires.txt",
        images="app cron tunnel clean".split(),
        app_branch="master",
        aws_id=None,
        newrelic_id=None,
        sentry_id=None,
    ):
        self.name = name
        self.project = project or name
        self.profile = profile
        self.regions = regions[:]
        self.psql_version = psql_version
        self.app_branch = app_branch
        self.python_version = python_version
        self.requires_name = requires_name
        self.images = images
        self.aws_id = aws_id
        self.newrelic_id = newrelic_id
        self.sentry_id = sentry_id

    @classmethod
    def load_clusters(cls, config_dict: Dict):
        result = {}
        for i_name, i_details in config_dict.items():
            profile = i_details.pop("profile", i_name)
            result[i_name] = cls(name=i_name, profile=profile, **i_details)
        cls.clusters = result
        return cls.clusters

    @property
    def caption(self):
        return self.name.upper()

    PROJECT_MAP = {"t3can": "tier3"}

    CLUSTERS_ARG = [
        ("/ami.unhaggle", ["unhaggle-ami"]),
        ("/audi-cluster", ["tier1_audi"]),
        ("/bp-cluster", ["buildandprice"]),
        ("/buildandprice", ["buildandprice"]),
        ("/creditapp", ["t3can"]),
        ("/pi-cluster", ["mi-pi"]),
        ("/polestar", ["polestar"]),
        ("/polestar-cluster", ["polestar"]),
        ("/t3can-cluster", ["t3can"]),
        ("/t3usa-cluster", ["t3usa"]),
        ("/tier1_audi", ["tier1_audi"]),
        ("/tier1", ["tier1"]),
        ("/tier1-cluster", ["tier1"]),
        ("/tier3", ["tier3"]),
        ("/unhaggle", ["unhaggle"]),
        ("/unhaggle-ami", ["unhaggle-ami"]),
        ("/unhaggle-cluster", ["unhaggle"]),
        ("/mi-cluster", ["mi-dev"]),
    ]

    CLUSTER_MAP = {
        "audi": "tier1_audi",
        "bp": "buildandprice",
        "dev": "mi-dev",
        "intranet": "internal",
        "nomad": "internal",
        "pi": "mi-pi",
        "qa": "mi-qa",
        "ps": "mi-qa",
        "perf": "mi-qa",
        "sandbox": "mi-sandbox",
        "stage": "mi-stage",
    }

    @classmethod
    def clusters_arg(cls, clusters):
        result = clusters
        if not result:
            cwd = os.getcwd()
            for i_match, i_clusters in cls.CLUSTERS_ARG:
                if i_match in cwd is not None:
                    result = i_clusters
                    break
            else:
                result = ["unhaggle-ami"]
        return result

    @classmethod
    def instances_arg(cls, instance_seed):
        name_parts = instance_seed.split("-")
        suffix = ""

        if instance_seed.startswith("i-"):
            return None, instance_seed

        last_part = name_parts.pop(-1)
        if last_part.isnumeric():
            suffix = f"-{last_part}"
            role = name_parts.pop(-1)
        else:
            role = last_part

        workspace = name_parts.pop(-1) if name_parts else cls.terraform_workspace()
        project = cls.clusters_arg([name_parts.pop(-1)] if name_parts else [])[0]
        cluster = cls.CLUSTER_MAP.get(workspace, cls.CLUSTER_MAP.get(project, project))
        cluster = cls.clusters[cluster]
        project = cls.PROJECT_MAP.get(project, project)
        return cluster, f"{project}-{workspace}-{role}{suffix}"

    @classmethod
    def terraform_workspace(cls):
        return (
            subprocess.check_output(["terraform", "workspace", "show"])
            .decode("UTF-8")
            .strip()
        )

    def regions_arg(self, regions, force=False):
        """
        Handles regions argument.
        """
        if "*" in regions:
            return tuple(self.regions)

        if not regions:
            return (self.regions[0],)

        if isinstance(regions, str):
            regions = regions.split(",")

        if not force:
            invalid_regions = [i for i in regions if i not in self.regions]
            if invalid_regions:
                raise RuntimeError(
                    f"Invalid regions: {', '.join(invalid_regions)}. Valid ones {', '.join(self.regions)}"
                )
        return tuple(regions)

    def image_names_arg(self, images):
        """
        Handles images argument:
            * If given, check each image name and return it;
            * If not given, return the complete list of images for this cluster.
        """
        if not images or images == "*":
            return self.images

        if isinstance(images, str):
            images = images.split(",")

        invalid_images = [i for i in images if i not in self.images]
        if invalid_images:
            raise RuntimeError(
                f"Invalid images: {', '.join(invalid_images)}. Valid images: {', '.join(self.images)}"
            )
        return images

    @functools.lru_cache()
    def codedeploy(self, region=None):
        region = region or self.regions[0]
        return self._session.client("codedeploy", region_name=region)

    @functools.lru_cache()
    def s3(self, region=None):
        region = region or self.regions[0]
        return self._session.client("s3", region_name=region)

    @functools.lru_cache()
    def ec2(self, region=None):
        region = region or self.regions[0]
        return self._session.client("ec2", region_name=region)

    @functools.lru_cache()
    def autoscaling(self, region=None):
        region = region or self.regions[0]
        return self._session.client("autoscaling", region_name=region)

    @functools.lru_cache()
    def ec2_resource(self, region=None):
        region = region or self.regions[0]
        return self._session.resource("ec2", region_name=region)

    @functools.lru_cache()
    def ec2_client(self, region=None):
        region = region or self.regions[0]
        return self._session.client("ec2", region_name=region)

    @functools.lru_cache()
    def ecs_client(self, region=None):
        region = region or self.regions[0]
        return self._session.client("ecs", region_name=region)

    @functools.lru_cache()
    def ecr_client(self, region=None):
        region = region or self.regions[0]
        return self._session.client("ecr", region_name=region)

    @functools.lru_cache()
    def ssm_client(self, region=None):
        region = region or self.regions[0]
        return self._session.client("ssm", region_name=region)

    @functools.lru_cache()
    def ssm_resource(self, region=None):
        region = region or self.regions[0]
        return self._session.client("ssm", region_name=region)

    @property
    @functools.lru_cache()
    def _session(self):
        return boto3.Session(profile_name=self.profile)

    @functools.lru_cache()
    def list_images(self, regions=None):
        """
        List AMI images for this cluster.
        Return a list of dictionary with the keys defined in image_keys.
        """
        result = []
        regions = regions or self.regions
        for i_region in regions:
            for i in self.ec2_resource(i_region).images.filter(Owners=self.AWS_OWNERS):
                image = Image.from_aws_ami(i, region=i_region, profile=self.profile)
                result.append(image)
        return result

    @functools.lru_cache()
    def list_instances(self, region, sort_by="launch_time"):
        ec2 = self.ec2_resource(region)
        return [
            Instance(self, region, i)
            for i in sorted(ec2.instances.filter(), key=attrgetter(sort_by))
        ]

    def get_image(self, image_name, version, region, image_os):
        for i_image in self.list_images():
            try:
                if i_image.tag_name == "-":
                    tag_name, tag_version = i_image.name.split("-", 3)[-2:]
                else:
                    tag_name, tag_version = (
                        i_image.tag_name,
                        i_image.tag_version,
                    )
                if (
                    i_image.region == region
                    and tag_name == image_name
                    and tag_version == version
                ):
                    return i_image
            except ValueError:
                # Ignore images that don't match our format.
                continue
        return Image(
            tag_name=image_name,
            tag_version=version,
            profile=self.profile,
            region=region,
            image_os=image_os,
        )

    def get_instance_by_name(self, instance_name, state="running"):
        region = self.regions[0]
        result = self.ec2_resource(region).instances.filter(
            Filters=[
                {"Name": "tag:Name", "Values": [f"{instance_name}*"]},
                {"Name": "instance-state-name", "Values": [state]},
            ]
        )
        return list(result)

    def copy_image(self, source_image, region, yes=False):
        result = copy.deepcopy(source_image)
        result.image_id = None
        result.region = region

        if not yes:
            print(
                f"$ aws ec2 copy-image {source_image.display_name} ==> {result.region}"
            )
            return result

        response = self.ec2(region).copy_image(
            Name=source_image.name,
            SourceImageId=source_image.image_id,
            SourceRegion=source_image.region,
        )
        result.image_id = response["ImageId"]
        return result

    def wait_image_available(self, images, yes=False):
        """
        Wait for the given images to be available.
        """
        if yes:
            images_by_region = {}
            for i_image in images:
                images_by_region.setdefault(i_image.region, []).append(i_image)

            for i_region, i_images in images_by_region.items():
                waiter = self.ec2(i_region).get_waiter("image_available")
                waiter.wait(
                    ImageIds=[j.image_id for j in i_images],
                    WaiterConfig={"Delay": 6, "MaxAttempts": 100},
                )
        else:
            print("$ aws ec2 wait image-available:")
            for i_image in images:
                print(f"  * {i_image.display_name}")

    def build_image(
        self,
        image,
        base_ami_version=None,
        ami_regions=None,
        ami_users=None,
        image_os="centos7",
        aws_credentials=",",
        yes=False,
    ):
        """
        Build the image using packer.
        The configuration files are expected at
          build-amis/<OS>/NAME/
        """
        vars = dict(
            version=image.tag_version,
            app_branch=self.app_branch,
            app_name=self.name,
            aws_profile=self.profile,
            aws_region=self.regions[0],
            base_ami_version=base_ami_version or image.tag_version,
            psql_version=self.psql_version,
            python_version=self.python_version,
            requires_name=self.requires_name,
            # Credentials to download stuff from S3 from the builder EC2
            # instance. Couldn't find a way to use the instances permissions
            # using IAM.
            aws_access_key=aws_credentials.split(",")[0],
            aws_secret_key=aws_credentials.split(",")[1],
        )

        filters = {
            "cluster": [
                "version",
                "aws_profile",
                "aws_region",
            ],
            "base": [
                "version",
                "aws_profile",
                "aws_region",
            ],
            "basedocker": [
                "version",
                "base_ami_version",
                "aws_profile",
                "aws_access_key",
                "aws_secret_key",
                "aws_region",
            ],
            "app": [
                "version",
                "base_ami_version",
                "aws_profile",
                "aws_access_key",
                "aws_secret_key",
                "aws_region",
            ],
            "clean": [
                "version",
                "base_ami_version",
                "aws_profile",
                "aws_region",
                "app_name",
                "app_branch",
                "python_version",
                "requires_name",
                "psql_version",
            ],
            "ftp": [
                "version",
                "base_ami_version",
                "aws_profile",
            ],
            "tunnel": [
                "version",
                "base_ami_version",
                "aws_profile",
            ],
            "nomad": [
                "version",
                "base_ami_version",
                "aws_profile",
                "aws_region",
            ],
            "redash": [
                "version",
                "base_ami_name" "base_ami_version",
                "aws_profile",
                "aws_region",
            ],
        }
        vars = {
            i_name: i_value
            for i_name, i_value in vars.items()
            if i_name in filters[image.tag_name]
        }

        if ami_users:
            vars["ami_users"] = ami_users

        if ami_regions:
            vars["ami_regions"] = ami_regions

        return packer(
            "build",
            f"./{image_os}/{image.tag_name}/{image.tag_name}.pkr.hcl",
            builder="amazon-ebs",
            on_error="cleanup",
            vars=vars,
            yes=yes,
        )

    def list_deploy(self, revision_width=80):
        result = []
        for i_region in self.regions:
            apps = self.codedeploy(i_region).list_applications().get("applications", [])
            for j_app in apps:
                deployment_groups = self.codedeploy(i_region).list_deployment_groups(
                    applicationName=j_app
                )
                for k_group in deployment_groups.get("deploymentGroups", []):
                    deployment_group_info = (
                        self.codedeploy(i_region)
                        .get_deployment_group(
                            applicationName=j_app, deploymentGroupName=k_group
                        )
                        .get("deploymentGroupInfo", {})
                    )
                    last_deployment = deployment_group_info.get(
                        "lastAttemptedDeployment", {}
                    )

                    if not last_deployment:
                        continue

                    deployment = self.codedeploy(i_region).get_deployment(
                        deploymentId=last_deployment["deploymentId"]
                    )
                    deployment_info = deployment["deploymentInfo"]

                    try:
                        revision = deployment_info["revision"]["s3Location"]["key"]
                        revision = revision[:revision_width] + "..."
                    except KeyError:
                        revision = "UNKNOWN"

                    result.append(
                        dict(
                            cluster=self.name,
                            region=i_region,
                            app=j_app,
                            group=k_group,
                            status=deployment_info["status"],
                            create_time=format_date(deployment_info["createTime"]),
                            end_time=format_date(deployment_info.get("endTime", "")),
                            revision=revision,
                        )
                    )
        return result


def list_autoscaling_groups(asg_filter, region="ca-central-1"):
    """
    Returns a list of dictionary representing autoscaling groups with some
    extra information:

    * [ImageId]: The AMI id associated with the ASG.
    * [Instances]: A list of associated EC2 instances.
    * [InstanceRefreshes]: A list of associated instance refreshes.
    * start_instance_refresh: A method that starts the instance-refresh.
    """

    class ASG(dict):
        def __init__(self, *args, **kwargs):
            result = super().__init__(*args, **kwargs)
            ec2_client = session.client("ec2")

            if "LaunchConfigurationName" in self:
                launch_configurations = autoscaling.describe_launch_configurations(
                    LaunchConfigurationNames=[self["LaunchConfigurationName"]]
                )["LaunchConfigurations"]
                image_id = launch_configurations[0]["ImageId"]
            else:
                launch_template_id = self["LaunchTemplate"]["LaunchTemplateId"]
                launch_template = ec2_client.describe_launch_templates(
                    LaunchTemplateIds=[launch_template_id]
                )
                launch_template_version = launch_template["LaunchTemplates"][0][
                    "LatestVersionNumber"
                ]
                launch_template_version = ec2_client.describe_launch_template_versions(
                    LaunchTemplateId=launch_template_id,
                    Versions=[str(launch_template_version)],
                )
                image_id = launch_template_version["LaunchTemplateVersions"][0][
                    "LaunchTemplateData"
                ]["ImageId"]

            self["ImageId"] = image_id
            image_name = ec2_client.describe_images(ImageIds=[image_id])
            try:
                self["ImageName"] = image_name["Images"][0]["Name"]
            except (IndexError, KeyError):
                self["ImageName"] = "?"

            try:
                elb_health = {
                    i["Target"]["Id"]: i["TargetHealth"]["State"]
                    for i in elb.describe_target_health(
                        TargetGroupArn=self["TargetGroupARNs"][0]
                    )["TargetHealthDescriptions"]
                }
            except IndexError:
                elb_health = {}

            instance_ids = [j["InstanceId"] for j in self["Instances"]]
            if instance_ids:
                ec2_instances = {
                    j.instance_id: j
                    for j in ec2.instances.filter(InstanceIds=instance_ids)
                }
                for j_instance in self["Instances"]:
                    instance_id = j_instance["InstanceId"]
                    j_instance["ec2.ImageId"] = ec2_instances[instance_id].image_id
                    j_instance["ec2.State"] = get_resource_attr(
                        ec2_instances[instance_id], "state:Name"
                    )
                    j_instance["image.name"] = get_resource_attr(
                        ec2_instances[instance_id], "image.name"
                    )
                    j_instance["elb.HealthStatus"] = elb_health.get(instance_id, "?")

            instance_refreshes = autoscaling.describe_instance_refreshes(
                AutoScalingGroupName=asg_name
            )
            instance_refreshes = instance_refreshes["InstanceRefreshes"]
            self["InstanceRefreshes"] = instance_refreshes

            return result

        def start_instance_refresh(self):
            """
            Replaces instances using ASG "instance refresh" feature.
            """
            asg_name = self["AutoScalingGroupName"]
            return autoscaling.start_instance_refresh(
                AutoScalingGroupName=asg_name,
                Strategy="Rolling",
                Preferences={
                    "MinHealthyPercentage": 50,
                    "InstanceWarmup": 120,
                    # 'CheckpointPercentages': [50,],
                    # 'CheckpointDelay': 60
                },
            )

        def update(self, desired_capacity, max_size):
            """
            Replaces instances using a custom algorithm:
                * DOUBLE the number of instances;
                * WAIT for the new instances to take over;
                * HALVE the number of instances back to normal;
            """
            autoscaling.update_auto_scaling_group(
                AutoScalingGroupName=self["AutoScalingGroupName"],
                DesiredCapacity=desired_capacity,
                MaxSize=max_size,
            )

    PROFILE_MAP = {
        "sandbox": "mi-sandbox",
        "dev": "mi-dev",
        "stage": "mi-stage",
        "qa": "mi-qa",
        "peb": "tier3",
    }

    profile_name = asg_filter.split("-")
    profile_name = PROFILE_MAP.get(
        profile_name[1], PROFILE_MAP.get(profile_name[0], profile_name[0])
    )

    session = boto3.Session(profile_name=profile_name, region_name=region)
    autoscaling = session.client("autoscaling")
    ec2 = session.resource("ec2")
    elb = session.client("elbv2")
    result = []
    for i_autoscaling_group in autoscaling.describe_auto_scaling_groups()[
        "AutoScalingGroups"
    ]:
        asg_name = i_autoscaling_group["AutoScalingGroupName"]
        if not asg_name.startswith(asg_filter):
            continue

        autoscaling_group = ASG(i_autoscaling_group)
        result.append(autoscaling_group)

    if not result:
        print(f"WARNING: No autoscaling group matches the given name: {asg_filter}")

    return result


def handle_instance_refreshes(asg):
    """
    Handles instace-refreshes associated with the given ASG.

    Returns True if there's any instance-refresh in progress.
    """
    result = False
    for j_refresh in asg["InstanceRefreshes"]:
        if j_refresh["Status"] in ["Pending", "InProgress"]:
            result = True
            print(
                f"  >> NOTICE: Instance refresh in progress: {j_refresh.get('StatusReason', '')}"
            )
        elif j_refresh["Status"] == "Successful":
            # Ignore successful instance refreshes.
            pass
        else:
            raise RuntimeError(f"Instance refresh in an unkonwn state: {j_refresh}")
    return result


def handle_autoscaling_instances(asg, image_id_asg):
    """
    Check if any instance associated with the ASG is running with a AMI
    different from the one specificed on ASG.

    Returns whether the ASG needs refresh.
    """

    STATUS = {
        True: "outdated",
        False: "ok",
    }

    result = False
    for j_instance in asg["Instances"]:
        outdated = j_instance["ec2.ImageId"] != image_id_asg
        status = STATUS[outdated]
        result = result or outdated
        print(
            f"  - {j_instance['InstanceId']} ({j_instance['image.name']}): {j_instance.get('elb.HealthStatus', '?')} {j_instance['ec2.State']} ==>  {status} ",
        )
    return result
