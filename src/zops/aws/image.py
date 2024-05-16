import boto3

from .utils import get_resource_attr


class Image:
    """
    Encapsulates a AMI Image object with the following characteristics:

    * Only holds a subset of boto3's ami object;
    * This object has two modes:
      * One, reflects an existing AMI in a AWS cluster (image_id is not None);
      * The other, it holds information for objects not yet available on AWS.
    * This object fullfil the following objectives:
      * List AMI images;
      * Build, Copy, Tag and Share images.
    """

    _ATTRS = [
        "image_id",
        "image_os",
        "name",
        ("tag_name", "tags:Name"),
        ("tag_version", "tags:Version"),
        "owner_id",
        "creation_date",
        "state",
        # Meta information
        "profile",
        "region",
    ]

    def __init__(self, **kwargs):
        for i_name, i_seed in self._iter_attrs():
            setattr(self, i_name, kwargs.get(i_name))

    def __str__(self):
        return f"<Image {self.display_name} profile={self.profile} image_id={self.image_id}>"

    @classmethod
    def _iter_attrs(cls):
        for i_attr in cls._ATTRS:
            if not isinstance(i_attr, tuple):
                i_attr = (i_attr, i_attr)
            yield i_attr

    @classmethod
    def from_image_id(cls, session, image_id):
        return cls.from_aws_ami(session.resource("ec2").Image(image_id))

    @classmethod
    def from_aws_ami(cls, aws_ami, region="INVALID", profile="INVALID"):
        """
        Create an Image instance from a AWS AMI instance.
        """
        d = {}
        for i_name, i_seed in cls._iter_attrs():
            d[i_name] = get_resource_attr(aws_ami, i_seed)
        d.update(
            {
                "region": region,
                "profile": profile,
            }
        )
        return cls(**d)

    def split_name(self):
        assert self.name is not None
        result = self.name.split("-")[2:4]
        if len(result) == 1:
            result = ["", result[0]]
        return result

    @property
    def exists(self):
        return self.image_id is not None

    @property
    def tagged(self):
        return self.tag_name is None or self.tag_version is None

    @property
    def full_name(self):
        return (
            self.name
            or f"motoinsight-{self.image_os}-{self.tag_name}-{self.tag_version}"
        )

    @property
    def display_name(self):
        return f"{self.full_name} @ {self.profile}:{self.region}"

    def msg(self, msg):
        """
        Print a message prefixed with this image name and region.
        """
        print(f"* {self.display_name}: {msg}")

    def share_with(self, aws_id, yes=False):
        """
        Share this image with the target account.
        """
        if not yes:
            print(
                f"$ aws ec2 modify-image_attribute {self.full_name} ==> Add UserId={aws_id}"
            )
            return

        session = boto3.Session(profile_name=self.profile, region_name=self.region)
        ec2 = session.client("ec2")
        ec2.modify_image_attribute(
            ImageId=self.image_id,
            LaunchPermission=dict(Add=[dict(UserId=str(aws_id))]),
        )

    def deregister(self, yes=False):
        if not self.exists:
            return

        if not yes:
            print(f"$ aws ec2 deregister-image --image-id={self.image_id}")
            return

        session = boto3.Session(profile_name=self.profile, region_name=self.region)
        ec2 = session.client("ec2")
        ec2.deregister_image(ImageId=self.image_id)

    def auto_tag(self, yes=False):
        """
        Update 'Name' and 'Version' tags based on image name.
        """
        if not yes:
            print("$ aws ec2 create-tags...")
            return

        if not self.exists:
            self.msg("ERROR: Image does not exist on AWS Cluster.")
            return

        if self.tagged:
            self.msg("NOTE: Image already tagged.")
            return

        self.msg("TAG")

        session = boto3.Session(profile_name=self.profile, region_name=self.region)
        ec2_client = session.client("ec2")
        tag_name, tag_version = self.full_name.split("-")[2:4]
        ec2_client.create_tags(
            Resources=[self.image_id],
            Tags=[
                {"Key": "Name", "Value": tag_name},
                {"Key": "Version", "Value": tag_version},
            ],
        )
