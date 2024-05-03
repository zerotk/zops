import functools
from typing import Any

import boto3


class AwsProvider:
    """
    Encapsulate access to AWS API so we can mock it for testing.
    """

    def __init__(self, profile: str, region: str):
        self.__profile: str = profile
        self.__region: str = region

    @classmethod
    @functools.cache
    def singleton(cls, profile: str, region: str) -> "AwsProvider":
        return cls(profile, region)

    @property
    def profile(self) -> str:
        return self.__profile

    @property
    def region(self) -> str:
        return self.__region

    @property
    def session(self) -> boto3.Session:
        return boto3.Session(profile_name=self.profile, region_name=self.region)

    def ecr_client(self) -> Any:
        return self.session.client("ecr")

    def ecs_client(self) -> Any:
        return self.session.client("ecs")

    def logs_client(self) -> Any:
        return self.session.client("logs")

    def ssm_client(self) -> Any:
        return self.session.client("ssm")

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

    def get_parameters(self, parameter_prefix):
        ssm_client = self.ssm_client()
        parameters_pages = ssm_client.get_paginator("get_parameters_by_path").paginate(
            Path=parameter_prefix,
            Recursive=True,
            WithDecryption=True,
        )
        result = {}
        for i_page in parameters_pages:
            for j_parameter in i_page["Parameters"]:
                result[j_parameter["Name"]] = (
                    j_parameter.get("Value"),
                    j_parameter.get("Type"),
                )
        return result
