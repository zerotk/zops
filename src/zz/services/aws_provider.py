from typing import Any

import boto3
from botocore import exceptions

from zerotk import deps
from zz.services.console import Console


@deps.define
class AwsParameter:
    name: str = deps.field()
    value: str = deps.field()
    type_: str = deps.field()


@deps.define
class AwsProvider:
    """
    Encapsulate access to AWS API so we can mock it for testing.
    """

    parameter_factory = deps.Factory(AwsParameter)

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

    def sqs_client(self) -> Any:
        return self.session.client("sqs")

    def ecs_client(self) -> Any:
        return self.session.client("ecs")

    def logs_client(self) -> Any:
        return self.session.client("logs")

    def ssm_client(self) -> Any:
        return self.session.client("ssm")

    def get_available_profiles(self):
        return self.session.available_profiles

    def run_task(self, cluster, taskdef, *args):
        # Starts the task.
        ecs_client = self.ecs_client()
        r = ecs_client.run_task(
            cluster=cluster,
            taskDefinition=taskdef,
            overrides=dict(containerOverrides=[dict(name=taskdef, command=args)]),
        )
        try:
            task_id = r["tasks"][0]["taskArn"]
            task_id = task_id.split("/")[-1]
        except (IndexError, KeyError):
            raise RuntimeError(
                f"Error while handling output for run_task for task {taskdef} on cluster {cluster}: {r}"
            )

        # Wait for the task execution
        waiter = ecs_client.get_waiter("tasks_stopped")
        waiter.wait(cluster=cluster, tasks=[task_id])

        # Get the task logs.
        logs_client = self.logs_client()
        result = logs_client.get_log_events(
            logGroupName=taskdef,
            logStreamName=f"{taskdef}/{taskdef}/{task_id}",
        )
        result = [i["message"] for i in result["events"]]
        result = "\n".join(result)
        return result

    def get_parameters(self, parameter_prefix) -> list[dict]:
        ssm_client = self.ssm_client()
        parameters_pages = ssm_client.get_paginator("get_parameters_by_path").paginate(
            Path=parameter_prefix,
            Recursive=True,
            WithDecryption=True,
        )
        result = []
        for i_page in parameters_pages:
            for j_parameter in i_page["Parameters"]:
                result.append(
                    dict(
                        name=j_parameter["Name"],
                        value=j_parameter.get("Value"),
                        type_=j_parameter.get("Type"),
                    )
                )
        return result


@deps.define
class Instance:
    """
    Wraps boto3.ec2.Instance object so we can add more attributes to it (like image)
    """

    boto_instance: object

    def __getattr__(self, name):
        # DEBUG:
        # print(f"Instance.__getattr__({name})")
        return getattr(self.boto_instance, name)


@deps.define
class Cloud:

    aws_factory = deps.Factory(AwsProvider)
    instance_factory = deps.Factory(Instance)

    profile_name: str
    region: str

    @property
    def _aws(self):
        return self.aws_factory(profile=self.profile_name, region=self.region)

    @property
    def account_id(self):
        try:
            client = self._aws.sts_client()
            result = client.get_caller_identity()['Account']
        except exceptions.NoCredentialsError:
            result = "<NO CREDENTIALS>"
        except Exception as e:
            result = str(e)
        return result

    def list_ec2_instances(self, sort_by="launch_time"):
        import operator
        ec2 = self._aws.ec2_resource()
        result = [
            self.instance_factory(i)
            for i
            in sorted(ec2.instances.filter(), key=operator.attrgetter(sort_by))
        ]
        # Add 'image' attribute to all instances.
        images = {i.image_id: i for i in ec2.images.filter(Owners=["self"])}
        # DEBUG:
        # print(f"images: {images}")
        for i in result:
            image = images.get(i.image_id, None)
            # DEBUG:
            # print(f"image: {image}")
            i.image = image
        return result

    def list_ami_images(self, sort_by="creation_date"):
        """
        TODO: How to configure owners as a list of known accounts?
        """
        import operator
        ec2 = self._aws.ec2_resource()
        return [
            i
            for i
            in sorted(ec2.images.filter(Owners=["self"]), key=operator.attrgetter(sort_by))
        ]

    def as_dict(self):
        return dict(
            profile_name=self.profile_name,
            region=self.region,
            account_id=self.account_id,
        )


@deps.define
class AwsLocal:

    aws_local = deps.Singleton(AwsProvider, kwargs=dict(profile=None, region=None))
    cloud_factory = deps.Factory(Cloud)

    def list_clouds(self):
        for i_profile in self.aws_local.get_available_profiles():
            yield self.cloud_factory(profile_name=i_profile)
