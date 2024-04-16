import boto3
from .utils import get_resource_attr


class Instance:
    """
    WIP: Move Instance related functions to this class.
    """

    _ATTRS = [
        "instance_id",
        "state:Name",
        "tags:Name",
        "image.id",
        "image.name",
        "image.creation_date",
        "profile",
        "region",
        "launch_time",
    ]

    def __init__(self, cluster, region, boto3_instance):
        self.__cluster = cluster
        self.__region = region
        self.__instance = boto3_instance

    def as_row(self, keys):
        """
        Returns a list with the values of the given list of attributes.
        """
        extra_keys = {
            "profile": self.__cluster.profile,
            "region": self.__region,
        }
        return [
            extra_keys.get(k_key, False)
            or get_resource_attr(self.__instance, k_key)
            for k_key in keys
        ]

    def start(self):
        ec2_client = boto3.session.client("ec2")
        ec2_client.start_instance(
            instance_id=self.instance_id,
        )
        ec2_client.close()
