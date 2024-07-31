from typing import Any

import boto3
from botocore import exceptions

from zerotk import deps
from zz.services.console import Console


@deps.define
class AwsProvider:
    """
    Encapsulate access to AWS API so we can mock it for testing.
    """

    profile: str = deps.field()
    region: str = deps.field()

    @property
    def session(self) -> boto3.Session:
        return boto3.Session(profile_name=self.profile, region_name=self.region)

    def sts_client(self) -> Any:
        return self.session.client("sts")

    def ec2_resource(self) -> Any:
        return self.session.resource("ec2", region_name=self.region)

    def ecs_client(self) -> Any:
        return self.session.client("ecs")

    def ecs_client(self) -> Any:
        return self.session.client("ecs")

    def logs_client(self) -> Any:
        return self.session.client("logs")

    def ssm_client(self) -> Any:
        return self.session.client("ssm")

    def get_available_profiles(self):
        return self.session.available_profiles


@deps.define
class Cloud:

    aws = deps.Singleton(AwsProvider, request=True)

    profile_name: str

    @property
    def account_id(self):
        try:
            client = self.aws.sts_client()
            result = client.get_caller_identity()['Account']
        except exceptions.NoCredentialsError:
            result = "<NO CREDENTIALS>"
        except Exception as e:
            result = str(e)
        return result

    def list_ec2_instances(self, sort_by="launch_time"):
        import operator
        ec2 = self.aws.ec2_resource()
        return [i for i in sorted(ec2.instances.filter(), key=operator.attrgetter(sort_by))]

    def as_dict(self):
        return dict(
            profile_name=self.profile_name,
            account_id=self.account_id,
        )


@deps.define
class AwsParameter:
    name: str = deps.field()
    value: str = deps.field()
    type_: str = deps.field()


@deps.define
class AwsLocal:

    aws_local = deps.Singleton(AwsProvider, kwargs=dict(profile=None, region=None))
    cloud_factory = deps.Factory(Cloud)

#     def run_task(self, cluster, taskdef, *args):
#         # Starts the task.
#         ecs_client = self.ecs_client()
#         r = ecs_client.run_task(
#             cluster=cluster,
#             taskDefinition=taskdef,
#             overrides=dict(containerOverrides=[dict(name=taskdef, command=args)]),
#         )
#         try:
#             task_id = r["tasks"][0]["taskArn"]
#             task_id = task_id.split("/")[-1]
#         except (IndexError, KeyError):
#             raise RuntimeError(
#                 f"Error while handling output for run_task for task {taskdef} on cluster {cluster}: {r}"
#             )
#
#         # Wait for the task execution
#         waiter = ecs_client.get_waiter("tasks_stopped")
#         waiter.wait(cluster=cluster, tasks=[task_id])
#
#         # Get the task logs.
#         logs_client = self.logs_client()
#         result = logs_client.get_log_events(
#             logGroupName=taskdef,
#             logStreamName=f"{taskdef}/{taskdef}/{task_id}",
#         )
#         result = [i["message"] for i in result["events"]]
#         result = "\n".join(result)
#         return result
#
#     def get_parameters(self, parameter_prefix) -> list[AwsParameter]:
#         ssm_client = self.ssm_client()
#         parameters_pages = ssm_client.get_paginator("get_parameters_by_path").paginate(
#             Path=parameter_prefix,
#             Recursive=True,
#             WithDecryption=True,
#         )
#         result = []
#         for i_page in parameters_pages:
#             for j_parameter in i_page["Parameters"]:
#                 result.append(
#                     self.parameter_factory(
#                         name=j_parameter["Name"],
#                         value=j_parameter.get("Value"),
#                         type_=j_parameter.get("Type"),
#                     )
#                 )
#         return result

    def list_clouds(self):
        for i_profile in self.aws_local.get_available_profiles():
            yield self.cloud_factory(profile_name=i_profile)
