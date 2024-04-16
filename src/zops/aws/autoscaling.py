import boto3

from .image import Image
from .utils import get_resource_attr


class AutoScalingGroup:

    PROFILE_MAP = {}

    @classmethod
    def list_groups(cls, asg_seed, region):
        """
        Returns a list of dictionary representing autoscaling groups with some
        extra information:

        * [ImageId]: The AMI id associated with the ASG.
        * [Instances]: A list of associated EC2 instances.
        * [InstanceRefreshes]: A list of associated instance refreshes.
        * start_instance_refresh: A method that starts the instance-refresh.
        """

        profile_name = asg_seed.split("-")
        profile_name = cls.PROFILE_MAP.get(
            profile_name[1],
            cls.PROFILE_MAP.get(profile_name[0], profile_name[0])
        )
        print(f"AWS_PROFILE={profile_name}")
        print(f"AWS_REGION={region}")
        session = boto3.Session(
            profile_name=profile_name,
            region_name=region
        )
        autoscaling = session.client("autoscaling")

        result = []
        autoscaling_groups = autoscaling.describe_auto_scaling_groups()
        for i_autoscaling_group in autoscaling_groups["AutoScalingGroups"]:
            asg_name = i_autoscaling_group["AutoScalingGroupName"]
            if not asg_name.startswith(asg_seed):
                continue
            autoscaling_group = cls(session, i_autoscaling_group)
            result.append(autoscaling_group)

        if not result:
            print(
                f"WARNING: No autoscaling group matches the given name: {asg_seed}"
            )

        return result

    def __init__(self, session, asg_dict):
        self._session = session
        ec2_resource = self._session.resource("ec2")
        elbv2_client = self._session.client("elbv2")
        autoscaling_client = self._session.client("autoscaling")

        self.name = asg_dict["AutoScalingGroupName"]
        self.desired_capacity = asg_dict["DesiredCapacity"]
        self.max_size = asg_dict["MaxSize"]

        image_id = self._get_image_id_from_launch_data(self._session, asg_dict)
        self.image = Image.from_image_id(session, image_id)

        # Create a map from ec2 instance id to their health status in this
        # autoscaling group.
        try:
            elb_health = {
                i["Target"]["Id"]: i["TargetHealth"]["State"]
                for i in elbv2_client.describe_target_health(
                    TargetGroupArn=asg_dict["TargetGroupARNs"][0]
                )["TargetHealthDescriptions"]
            }
        except IndexError:
            elb_health = {}

        # TODO: Replace these dicts wiht Instance objects.
        self._instances = asg_dict["Instances"]
        instance_ids = [i["InstanceId"] for i in self._instances]
        if instance_ids:
            ec2_instances = {
                j.instance_id: j
                for j in ec2_resource.instances.filter(InstanceIds=instance_ids)
            }
            for j_instance in self._instances:
                instance_id = j_instance["InstanceId"]
                j_instance["ec2.ImageId"] = ec2_instances[
                    instance_id
                ].image_id
                j_instance["ec2.State"] = get_resource_attr(
                    ec2_instances[instance_id], "state:Name"
                )
                j_instance["image.name"] = get_resource_attr(
                    ec2_instances[instance_id], "image.name"
                )
                j_instance["elb.HealthStatus"] = elb_health.get(
                    instance_id, "?"
                )

        instance_refreshes = autoscaling_client.describe_instance_refreshes(
            AutoScalingGroupName=self.name
        )
        self._instance_refreshes = instance_refreshes["InstanceRefreshes"]

    def print(self):
        """
        Check if any instance associated with the ASG is running with a AMI
        different from the one specificed on ASG.

        Returns whether the ASG needs refresh.
        """

        STATUS = {
            True: "outdated",
            False: "updated",
        }

        result = False
        print(
            f"\n{self.name} ({self.image.name}) - ({self.desired_capacity} of {self.max_size})"
        )
        for j_instance in self._instances:
            outdated = j_instance["ec2.ImageId"] != self.image.image_id
            status = STATUS[outdated]
            result = result or outdated
            print(
                f"  - {j_instance['InstanceId']} ({j_instance['image.name']}): {j_instance.get('elb.HealthStatus', '?')} {j_instance['ec2.State']} ==>  {status} ",
            )
        return result

    @classmethod
    def _get_image_id_from_launch_data(cls, session, asg_dict):
        autoscaling_client = session.client("autoscaling")
        ec2_client = session.client("ec2")

        if "LaunchConfigurationName" in asg_dict:
            launch_configurations = (
                autoscaling_client.describe_launch_configurations(
                    LaunchConfigurationNames=[
                        asg_dict["LaunchConfigurationName"]
                    ]
                )["LaunchConfigurations"]
            )
            return launch_configurations[0]["ImageId"]
        else:
            launch_template_id = asg_dict["LaunchTemplate"]["LaunchTemplateId"]
            launch_template = ec2_client.describe_launch_templates(
                LaunchTemplateIds=[launch_template_id]
            )
            launch_template_version = launch_template["LaunchTemplates"][0]["LatestVersionNumber"]
            launch_template_version = (
                ec2_client.describe_launch_template_versions(
                    LaunchTemplateId=launch_template_id,
                    Versions=[str(launch_template_version)],
                )
            )
            return launch_template_version["LaunchTemplateVersions"][0]["LaunchTemplateData"]["ImageId"]


    def start_instance_refresh(self):
        """
        Replaces instances using ASG "instance refresh" feature.
        """
        asg_name = self["AutoScalingGroupName"]
        return self._autoscaling_client.start_instance_refresh(
            AutoScalingGroupName=asg_name,
            Strategy="Rolling",
            Preferences={
                "MinHealthyPercentage": 50,
                "InstanceWarmup": 120,
                # 'CheckpointPercentages': [50,],
                # 'CheckpointDelay': 60
            },
        )

    def update(self, desired_capacity):
        """
        Replaces instances using a custom algorithm:
            * DOUBLE the number of instances;
            * WAIT for the new instances to take over;
            * HALVE the number of instances back to normal;
        """
        autoscaling_client = self._session.client("autoscaling")
        autoscaling_client.update_auto_scaling_group(
            AutoScalingGroupName=self.name,
            DesiredCapacity=desired_capacity,
            MaxSize=max(self.max_size, desired_capacity),
        )


# def handle_instance_refreshes(asg):
#     """
#     Handles instace-refreshes associated with the given ASG.
#
#     Returns True if there's any instance-refresh in progress.
#     """
#     result = False
#     for j_refresh in asg["InstanceRefreshes"]:
#         if j_refresh["Status"] in ["Pending", "InProgress"]:
#             result = True
#             print(
#                 f"  >> NOTICE: Instance refresh in progress: {j_refresh.get('StatusReason', '')}"
#             )
#         elif j_refresh["Status"] == "Successful":
#             # Ignore successful instance refreshes.
#             pass
#         else:
#             raise RuntimeError(
#                 f"Instance refresh in an unkonwn state: {j_refresh}"
#             )
#     return result
#
#
# def handle_autoscaling_instances(asg, image_id_asg):
#     """
#     Check if any instance associated with the ASG is running with a AMI
#     different from the one specificed on ASG.
#
#     Returns whether the ASG needs refresh.
#     """
#
#     STATUS = {
#         True: "outdated",
#         False: "ok",
#     }
#
#     result = False
#     for j_instance in asg["Instances"]:
#         outdated = j_instance["ec2.ImageId"] != image_id_asg
#         status = STATUS[outdated]
#         result = result or outdated
#         print(
#             f"  - {j_instance['InstanceId']} ({j_instance['image.name']}): {j_instance.get('elb.HealthStatus', '?')} {j_instance['ec2.State']} ==>  {status} ",
#         )
#     return result
