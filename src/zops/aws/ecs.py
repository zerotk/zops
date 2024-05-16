import os

import botocore


class EcsCluster:

    def __init__(self, ecs_client, name: str):
        self.__ecs_client: botocore.client.ECS = ecs_client
        self.name: str = name

    @classmethod
    def list(cls, cluster, region):
        ecs_client = cluster.ecs_client(region=region)
        clusters = ecs_client.list_clusters()["clusterArns"]
        result = ecs_client.describe_clusters(clusters=clusters)["clusters"]
        return [cls(ecs_client, i["clusterName"]) for i in result]

    def list_services(self):
        result = self.__ecs_client.list_services(cluster=self.name)["serviceArns"]
        return [EcsService(self.__ecs_client, i) for i in result]


class EcsService:

    def __init__(self, ecs_client, arn: str):
        self.__ecs_client = ecs_client
        self.arn = arn

    @property
    def name(self):
        return os.path.basename(self.arn)
