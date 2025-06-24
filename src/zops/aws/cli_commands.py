import itertools
import operator
import os
import re
import sys
import time
from operator import attrgetter
from operator import itemgetter
from pathlib import Path

import addict
import boto3
import click
from tabulate import tabulate

from zops.aws.autoscaling import AutoScalingGroup
from zops.aws.cli_config import load_config
from zops.aws.cluster import Cluster
from zops.aws.ecs import EcsCluster
from zops.aws.image import Image
from zops.aws.instance import Instance
from zops.aws.utils_click import STRING_LIST


@click.command(name="ami.list")
@click.argument("clusters", nargs=-1)
@click.option("--regions", type=STRING_LIST, default="*")
@click.option("--force-regions", is_flag=True)
@click.option(
    "--sort-by",
    default="creation_date",
    type=click.Choice(
        [
            "image_id",
            "name",
            "tags:Name",
            "tags:Version",
            "owner_id",
            "creation_date",
            "stage",
            "profile",
            "region",
        ],
        case_sensitive=True,
    ),
    help="Sort list by thie attribute. Default: creation_date",
)
def ami_list(clusters, regions, force_regions, sort_by):
    """
    List AMIs in a cluster.

    List images from all regions associated with that cluster.

    Examples:

    \b
      # List AMI images for tier3's cluster.
      $ uh aws ami.list tier3

    \b
      # List AMI images. Try to guess the cluster based on the current directory.
      $ uh aws ami.list
    """
    load_config()
    clusters = Cluster.clusters_arg(clusters)

    rows = [[i[1] for i in Image._iter_attrs()]]
    for i_cluster in clusters:
        cluster = Cluster.clusters[i_cluster]
        regions = cluster.regions_arg(regions, force=force_regions)
        for i_ami in sorted(
            cluster.list_images(regions=regions), key=attrgetter(sort_by)
        ):
            rows.append([getattr(i_ami, j_name) for j_name, _ in Image._iter_attrs()])

    print(tabulate(rows, headers="firstrow"))


@click.command()
@click.argument("name")
@click.argument("region")
@click.argument("credentials")
@click.option("--role_arn", default=None)
def aws_configure_profile(name, region, credentials, role_arn):
    """
    Configure AWS profile locally (~/.aws/credentials).

    Add a new profile in the local credentials file using the given name,
    region and credentials.

    The credentials format is the following:

      access-id,access-secret

    Example:
    \b
    $ uh ami configure-profile tier3 ca-central-1 $AWS_ACCOUNT_KEY_ID,$AWS_SECRET_ACCOUNT_KEY

    OUTPUT: ~/.aws/credentials file has new values like

    \b
    [tier3]
    aws_access_key_id=<value of $AWS_ACCOUNT_KEY_ID>
    aws_secret_access_key=<value of $AWS_SECRET_ACCOUNT_KEY>
    region = ca-central-1
    """
    load_config()
    credentials_file = Path("~/.aws/credentials").expanduser()
    credentials_file.parent.mkdir(parents=True, exist_ok=True)

    access_id, access_secret = credentials.split(",", 1)
    with credentials_file.open("a") as oss:
        oss.write(
            f"""
[{name}]
aws_access_key_id={access_id}
aws_secret_access_key={access_secret}
region = {region}"""
        )
        if role_arn:
            oss.write(
                f"""
role_arn={role_arn}
"""
        )


@click.command("ami.deregister")
@click.argument("cluster")
@click.argument("image_names", nargs=-1)
@click.option("--regions", type=STRING_LIST, default="*")
@click.option("--yes", is_flag=True)
def ami_deregister(cluster, image_names, regions, yes):
    """
    Deregister AMIs with the given version.
    """
    load_config()
    internal_cluster = Cluster.clusters[cluster]
    regions = ("ca-central-1", "us-east-2")

    def _items():
        """
        List items (image) to be deregistered.
        """
        result = []
        for i_image in internal_cluster.list_images(regions=regions):
            for j_image_name in image_names:
                m = re.match(j_image_name, i_image.name)
                if m is not None:
                    result.append(i_image)
        return result

    for i_image in _items():
        i_image.msg("DEREGISTER")
        i_image.deregister(yes=yes)


@click.command("ami.build")
@click.argument("version")
@click.argument(
    "cluster_name",
)
@click.argument("cluster_names", nargs=-1)
@click.option(
    "--images",
    "image_names",
    help="List images to build. By default build all images.",
    type=STRING_LIST,
    default=[],
)
@click.option(
    "--regions",
    help="Region where to build the AMI.\nBy default build on cluster's"
    "default region.",
    type=STRING_LIST,
    default=[],
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing image with the same name.",
)
@click.option(
    "--cleanedb-app_branch",
    default=None,
    help="Overrides clean machine application branch. Defaults to the image"
    "defined on aws_operations.yml configuration file.",
)
@click.option("--base-ami-version", default=None)
@click.option("--image-os", default="centos7")
@click.option("--aws-credentials-env", default="AWS_CREDENTIALS__AMI_BUILD")
@click.option("--yes", is_flag=True)
def ami_build(
    version,
    cluster_name,
    cluster_names,
    image_names,
    regions,
    overwrite,
    cleanedb_app_branch,
    base_ami_version,
    image_os,
    aws_credentials_env,
    yes,
):
    """
    Build AMIs base images.

    VERSION: The version (semantic) for the new base images.
    CLUSTER_NAME: Cluster where to build images.
    CLUSTER_NAMES: Optional list of clusters to share the image with.

    * This command must be executed on unhaggle/unhaggle-ami repository;
    * This command must be executed on build-amis directory;

    Examples:

    \b
      # Build version 2.0.10 for all baseimages
      $ uh aws ami.build 2.0.10

    \b
      # Build version 2.0.10 for all baseimages (explicit)
      $ uh aws ami.build 2.0.10 unhaggle-ami

    \b
      # Build version 2.0.10 for all baseimages and share it with tier3
      $ uh aws ami.build 2.0.10 unhaggle-ami tier3

    \b
      # Build version 2.0.10 only for baseimage
      $ uh aws ami.build --images=baseimage 2.0.10

    \b
      # Build version 2.0.10 for all baseimages on tier3 cluster
      $ uh aws ami.build 2.0.10 tier3

    \b
      # Build version 2.0.10 of clean image for tier3
      $ uh-ami ami.build --images=clean 2.0.10 tier3
    """
    load_config()
    cluster = Cluster.clusters[cluster_name]
    image_names = cluster.image_names_arg(image_names)
    regions = cluster.regions_arg(regions)

    cluster_names = set(cluster_names)
    clusters = [Cluster.clusters[i] for i in cluster_names]
    ami_regions = {i.regions[0] for i in clusters if i.regions[0] != cluster.regions[0]}
    ami_users = {str(i.aws_id) for i in clusters}
    base_ami_version = base_ami_version or version

    aws_credentials = os.environ[aws_credentials_env]

    print(
        f"""
# Build AMIs
  * cluster: {cluster.name}
  * regions: {', '.join(regions)}
  * ami_user: {', '.join(ami_users)}
  * images: {', '.join(image_names)}
  * version: {version}
  * aws_credentials: {aws_credentials}
  * base_ami_version: {base_ami_version}
"""
    )
    if ami_regions:
        print("# Copy AMIs to these regions:")
        for i_region in ami_regions:
            print(f"  * {i_region}")
        print("# Share with these AWS accounts:")
        for i_cluster in clusters:
            print(f"  * {i_cluster.aws_id} ({i_cluster.name})")

    def _items():
        """
        List items (image) to be build.
            * Check if the image already exists;
        """
        result = []
        for i_image_name, i_region in itertools.product(image_names, regions):
            image = cluster.get_image(i_image_name, version, i_region, image_os)
            if image.exists:
                if overwrite:
                    image.msg("WARN: Image already exists: Overwriting.")
                    image.deregister(yes=yes)
                else:
                    image.msg("SKIP: Image already exists: Skipping")
                    continue
            result.append(image)

        return result

    for i_image in _items():
        i_image.msg("BUILD")
        if cleanedb_app_branch is not None:
            cluster.app_branch = cleanedb_app_branch
        r = cluster.build_image(
            i_image,
            base_ami_version,
            ami_regions=ami_regions,
            ami_users=ami_users,
            image_os=image_os,
            aws_credentials=aws_credentials,
            yes=yes,
        )
        if not r:
            print(
                "ERROR: Error while building image. " "Check the logs for more details."
            )
            sys.exit(1)


@click.command()
@click.argument("clusters", nargs=-1)
@click.option("--revision_width", default=80)
def deployments_list(clusters, revision_width):
    """
    List AWS deployments.
    """
    load_config()
    keys = [
        "cluster",
        "region",
        "app",
        "group",
        "status",
        "create_time",
        "end_time",
        "revision",
    ]
    sort_by = "create_time"

    clusters = Cluster.clusters_arg(clusters)

    deploys = []
    for i_cluster in clusters:
        cluster = Cluster.clusters[i_cluster]
        deploys += cluster.list_deploy(revision_width=revision_width)

    rows = [keys]
    rows += [[i[j] for j in keys] for i in sorted(deploys, key=itemgetter(sort_by))]
    print(tabulate(rows, headers="firstrow"))


@click.command(name="ec2.list")
@click.argument("clusters", nargs=-1)
@click.option("--sort-by", default="launch_time")
@click.option("--volumes", is_flag=True)
@click.option("--keys", type=list, default=Instance._ATTRS)
def ec2_list(sort_by, volumes, keys, clusters):
    """
    List AWS EC2 instances.
    """
    load_config()
    clusters = Cluster.clusters_arg(clusters)

    if volumes:
        keys += ["encrypted_volumes"]

    rows = [keys]
    for i_cluster in clusters:
        cluster = Cluster.clusters[i_cluster]
        for i_region in cluster.regions:
            for j_instance in cluster.list_instances(i_region, sort_by=sort_by):
                rows.append(j_instance.as_row(keys))
    print(tabulate(rows, headers="firstrow"))


@click.command()
@click.argument("instance_names", nargs=-1)
def ec2_start(instance_names):
    """
    Start AWS EC2 instance.
    """
    load_config()
    CLUSTER_MAP = {
        "bp": "buildandprice",
        "audi": "tier1_audi",
    }

    for i_instance_name in instance_names:
        cluster = i_instance_name.split("-")[0]
        cluster = CLUSTER_MAP.get(cluster, cluster)
        cluster = Cluster.clusters[cluster]
        for j_instance in cluster.get_instance_by_name(
            i_instance_name, state="stopped"
        ):
            print(f"{j_instance}: Starting instance.")
            j_instance.start()


@click.command(name="ec2.shell")
@click.argument("instance_seed")
@click.option("--index", type=int, default=0)
@click.option("--profile", type=str, default=None)
@click.option("--region", default=None)
@click.option("--command", type=str, default=None)
@click.option("--sleep", type=int, default=1)
def ec2_shell(instance_seed, index, profile, region, command, sleep):
    """
    Start SSM session on AWS EC2 instance.
    """
    import os

    load_config()
    cluster, instance_name = Cluster.instances_arg(instance_seed)

    if cluster is None:
        instance_id = instance_name
    else:
        print(f"Instance name: {instance_name}")
        profile = profile or cluster.profile
        print(f"AWS profile: {profile}")
        if region is not None:
            cluster.regions = [region]
        else:
            region = cluster.regions[0]
        print(f"AWS region: {region}")
        instances = cluster.get_instance_by_name(instance_name, state="running")
        if not instances:
            print(
                f"""
ERROR: No instances found.

Check if your AWS credentials work with:
  aws --profile={profile} ec2 describe-instances
"""
            )
            exit(9)
        instance = instances[index]
        instance_id = instance.id
    print(f"Instance id: {instance_id}")

    if command:
        ssm_client = boto3.Session(profile_name=profile).client("ssm")
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [command]},
        )
        command_id = response["Command"]["CommandId"]
        for i_retries in range(3):
            time.sleep(sleep)
            output = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id,
            )
            if output["Status"] != "InProgress":
                break
        print(output["StandardOutputContent"])
    else:
        cmd = f"aws --profile={profile} ssm start-session --target {instance_id} --document-name AWS-StartInteractiveCommand --parameters command=\"bash -l\""
        print(f"Command line: {cmd}")
        os.system(cmd)  # nosec B605
        print(f"{instance_id}: Finished SSM session.")


@click.command(name="asg.list")
@click.argument("asg_seed")
@click.option("--profile", type=str, default=None)
@click.option("--region", default=None)
def asg_list(asg_seed, profile, region):
    """
    List ASGs (Auto Scaling Gropus) that matches the given name.

    Examples:
        # Lists all production ASGs for Tier3.
        uh aws asg.list tier3-prod
    """
    load_config()
    for i_asg in AutoScalingGroup.list_groups(
        asg_seed, profile_name=profile, region=region
    ):
        i_asg.print()


@click.command()
@click.argument("asg_seed")
def asg_instance_refresh(asg_seed):
    """
    Executes instance-refresh for ASGs

    Examples:
        # Update instances related with Tier3's production ASGs.
        uh aws asg.instance-refresh tier3-prod-app
    """
    from zops.aws.cluster import list_autoscaling_groups

    load_config()
    autoscaling_groups = list_autoscaling_groups(asg_seed)

    for i_asg in autoscaling_groups:
        asg_name = i_asg["AutoScalingGroupName"]
        i_asg.start_instance_refresh()
        print(f"\n{asg_name} >> SUCCESS: Instance refresh started.")


@click.command(name="asg.update")
@click.argument("asg_seed")
@click.argument("desired_capacity", type=int)
@click.option("--profile", type=str, default=None)
@click.option("--region", default=None)
def asg_update(asg_seed, desired_capacity, profile, region):
    """
    Updates the desired capacity for ASGs.

    Examples:
        # Update the desired capacity of tier3-prod-app to 6.
        uh aws asg.update tier3-prod-app 6
    """
    load_config()

    for i_asg in AutoScalingGroup.list_groups(
        asg_seed, profile_name=profile, region=region
    ):
        i_asg.print()
        i_asg.update(
            desired_capacity=desired_capacity,
        )


@click.command(name="params.list")
@click.argument("cluster")
@click.option("--prefix", default="/")
@click.option("--region", default=None)
def params_list(cluster, prefix, region):
    """
    List parameters from the selected cluster.

    Examples:
        uh aws params.list tier3
    """
    load_config()
    cluster = Cluster.get_cluster(cluster)
    if region is None:
        regions = cluster.regions
    else:
        regions = [region]
    result = {}
    for i_region in regions:
        ssm = cluster.ssm_client(i_region)
        parameters_pages = ssm.get_paginator("get_parameters_by_path").paginate(
            Path=prefix,
            Recursive=True,
            WithDecryption=True,
        )
        for i_page in parameters_pages:
            for j_parameter in i_page["Parameters"]:
                result[f"{cluster.name}:{i_region}:{j_parameter['Name']}"] = (
                    j_parameter.get("Value"),
                    j_parameter.get("Type"),
                )

    for i_name, (i_value, i_type) in sorted(result.items()):
        type_spec = f":{i_type}" if i_type != "String" else ""
        print(f"{i_name}{type_spec}={i_value}")


@click.command(name="params.put")
@click.argument("cluster")
@click.argument("filename")
@click.option("--region", default=None)
def params_put(cluster, filename, region):
    """
    Upload settings from filename into Parameter Store.
    Examples:
        uh aws params.put tier3-dev-params.lst
    """

    def parameters(filename):
        for i_line in open(filename).readlines():
            line = i_line.strip("\n ")
            if not line:
                continue
            if line.startswith("#"):
                continue
            yield split_name_value(line)

    load_config()
    cluster = Cluster.get_cluster(cluster)
    region = region or cluster.regions[0]
    ssm = cluster.ssm_resource(region)

    for i_name, i_type, i_value in parameters(filename):
        if i_type == "SecureString":
            value = "..." + i_value[-5:]
        else:
            value = i_value
        # print(f"DEL  {i_name}:{i_type}={value}")
        # print(f"NEW  {i_name}:{i_type}={value}")
        print(f"SET  {i_name}:{i_type}={value}")
        ssm.put_parameter(Name=i_name, Value=i_value, Type=i_type, Overwrite=True)


def split_name_value(name_value):
    NAME_VALUE_REGEX = re.compile(
        r"(?P<name>[\/\-\w]*)(?::(?P<type>\w*))?=(?P<value>.*)$"
    )
    m = NAME_VALUE_REGEX.match(name_value)
    if m is None:
        raise RuntimeError(f"Can't regex the line: '{name_value}'")
    r_name, r_type, r_value = m.groups()
    r_type = r_type or "String"
    return r_name, r_type, r_value


@click.command(name="params.get")
@click.argument("cluster")
@click.argument("name")
@click.option("--region", default=None)
def params_get(cluster, name, region):
    """
    Get the value of a SSM Parameter.
    Examples:
        uh aws params.get mi-dev /DJANGO/CREDITAPP_DEV__SLACK_TOKEN
    """
    load_config()
    cluster = Cluster.get_cluster(cluster)
    region = region or cluster.regions[0]
    ssm = cluster.ssm_resource(region)
    r = ssm.get_parameter(Name=name, WithDecryption=True)
    print("{name}:{Type}={Value}".format(name=name, **r["Parameter"]))


@click.command(name="params.set")
@click.argument("cluster")
@click.argument("name_values", nargs=-1)
@click.option("--region", default=None)
@click.option("--overwrite", is_flag=True)
def params_set(cluster, name_values, region, overwrite):
    """
    Set a SSM Parameter value.
    Examples:
        uh aws params.set tier3-dev /DJANGO/TIER3_DEV__SLACK_TOKEN=12345
    """
    load_config()
    cluster = Cluster.get_cluster(cluster)
    region = region or cluster.regions[0]
    ssm = cluster.ssm_resource(region)
    for i_name_value in name_values:
        name, value_type, value = split_name_value(i_name_value)
        ssm.put_parameter(Name=name, Value=value, Type=value_type, Overwrite=overwrite)


@click.command(name="params.del")
@click.argument("cluster")
@click.argument("names", nargs=-1)
@click.option("--region", default=None)
def params_del(cluster, names, region):
    """
    Delete a SSM Parameter.
    Examples:
        uh aws params.del tier3-dev /DJANGO/TIER3_DEV__SLACK_TOKEN
    """
    load_config()
    cluster = Cluster.get_cluster(cluster)
    region = region or cluster.regions[0]
    ssm = cluster.ssm_resource(region)
    for i_name in names:
        try:
            ssm.delete_parameter(Name=i_name)
            click.echo(f"* {i_name}: deleted")
        except ssm.exceptions.ParameterNotFound:
            click.echo(f"* {i_name}: parameter not found")


@click.command(name="resources.clean")
@click.argument("clusters", nargs=-1)
@click.option("--region", default=None)
@click.option("--yes", is_flag=True)
def resources_clean(clusters, region, yes):
    SECURITY_GROUP_FILTER = [
        {
            "Name": "description",
            "Values": ["Temporary group for Packer", "launch-wizard-*"],
        }
    ]
    KEYPAIRS_FILTER = [{"Name": "key-name", "Values": ["packer*"]}]

    load_config()
    for i_cluster in clusters:
        cluster = Cluster.get_cluster(i_cluster)
        region = region or cluster.regions[0]
        ec2 = cluster.ec2_resource(region)
        ec2_client = cluster.ec2_client()

        click.echo("Resources cleanup")

        click.echo("* Security Groups:")
        security_groups = ec2.security_groups.filter(Filters=SECURITY_GROUP_FILTER)
        for i in security_groups:
            click.echo(f"  * {i.group_id}: {i.group_name} - {i.description}")

        click.echo("* Key Pairs:")
        key_pairs = ec2.key_pairs.filter(Filters=KEYPAIRS_FILTER)
        for i in key_pairs:
            click.echo(f"  * {i.key_pair_id}: {i.key_name}")

        click.echo("* Instances:")
        INSTANCES_FILTER = [
            {
                "Name": "instance.group-id",
                "Values": [i.group_id for i in security_groups],
            }
        ]
        instances = ec2.instances.filter(Filters=INSTANCES_FILTER)
        for i in instances:
            name_tag = [j["Value"] for j in i.tags if j["Key"] == "Name"]
            if name_tag:
                name_tag = name_tag[0]
            else:
                name_tag = "<noname>"
            click.echo(f"  * {i.id}: {name_tag} - {i.state['Name']}")

        click.echo("* Volumes:")
        volumes_filter = {"Name": "status", "Values": ["available"]}
        volumes = ec2_client.describe_volumes(Filters=[volumes_filter])["Volumes"]
        for i in volumes:
            i = addict.Dict(i)
            click.echo(f"  * {i.VolumeId} - {i.State}")

        click.echo("* Snapshots:")
        images = ec2_client.describe_images(Owners=["self"])["Images"]
        images_snapshots = {}
        for i_image in images:
            for j_block_device in i_image["BlockDeviceMappings"]:
                images_snapshots[j_block_device["Ebs"]["SnapshotId"]] = i_image[
                    "ImageId"
                ]

        snapshots = ec2_client.describe_snapshots(OwnerIds=["self"])["Snapshots"]
        snapshots_to_delete = []
        for i in sorted(snapshots, key=operator.itemgetter("StartTime")):
            i = addict.Dict(i)
            if i.SnapshotId in images_snapshots:
                continue
            snapshots_to_delete.append(i.SnapshotId)
            click.echo(f"  * {i.StartTime} - {i.SnapshotId}")

        if yes:
            click.echo("Terminating instances...")
            for i in instances:
                i.terminate()

            click.echo("Deleting key-pairs...")
            for i in key_pairs:
                i.delete()

            click.echo("Deleting security-groups...")
            for i in security_groups:
                try:
                    i.revoke_ingress(IpPermissions=i.ip_permissions)
                    i.delete()
                except Exception:
                    click.echo(f"*** Failed to delete security group {i.id}")
                    continue

            click.echo("Deleting snapshots...")
            for i in snapshots_to_delete:
                try:
                    ec2_client.delete_snapshot(SnapshotId=i)
                except Exception:
                    click.echo(f"*** Failed to delete snapshot {i}")
                    continue


@click.command(name="resources.clear_default_vpcs")
@click.argument("cluster")
@click.option("--regions", multiple=True, default=[])
@click.option("--skip-regions", multiple=True, default=["ca-central-1", "us-east-2"])
@click.option("--yes", is_flag=True)
def resources_clear_default_vps(cluster, regions, skip_regions, yes):
    load_config()
    cluster = Cluster.get_cluster(cluster)
    client = cluster.ec2()
    regions = regions or [i["RegionName"] for i in client.describe_regions()["Regions"]]
    regions = [i for i in regions if i not in skip_regions]
    print(f"Regions: {regions}")
    for i_region in regions:
        ec2 = cluster.ec2_resource(i_region)
        for j_vpc in ec2.vpcs.all():
            vpc_name = "?"
            if j_vpc.tags:
                tags = {k["Key"]: k["Value"] for k in j_vpc.tags}
                vpc_name = tags["Name"]
            if not j_vpc.is_default:
                print(
                    f"* Skip non-default VPC in region {i_region}: {j_vpc.vpc_id} ({vpc_name})"
                )
                continue
            print(
                f"* Deleting default VPC in region {i_region}: {j_vpc.vpc_id} ({vpc_name})"
            )
            _delete_vpc(j_vpc, yes)


def _delete_vpc(vpc, yes):
    for igw in vpc.internet_gateways.all():
        print(f"  * Detaching and Removing igw: {igw.id}")
        if yes:
            igw.detach_from_vpc(VpcId=vpc.vpc_id)
            igw.delete()
    for sub in [i for i in vpc.subnets.all() if i.default_for_az]:
        print(f"  * Removing subnet: {sub.id}")
        if yes:
            sub.delete()
    for rtb in vpc.route_tables.all():
        if rtb.associations_attribute and rtb.associations_attribute[0]["Main"]:
            print(f"  * Skip main route-table: {rtb.id}")
            continue
        print(f"* Removing route-table {rtb.id}")
        if yes:
            rtb.delete()
    for acl in [i for i in vpc.network_acls.all() if not i.is_default]:
        print(f"  * Removing acl: {acl.id}")
        if yes:
            acl.delete()
    for sg in vpc.security_groups.all():
        if sg.group_name == "default":
            print(f"  * Skip default security group: {sg.id}")
            continue
        print(f"  * Removing security-group: {sg.id}")
        if yes:
            sg.delete()
    print(f"  * Removing vpc: {vpc.id}")
    if yes:
        vpc.delete()


@click.command(name="ecr.list")
@click.argument("repos", nargs=-1)
@click.option("--cluster", default="mi-shared")
@click.option("--region", default=None)
def ecr_list(repos, cluster, region):
    load_config()
    cluster = Cluster.get_cluster(cluster)
    region = region or cluster.regions[0]
    ecr = cluster.ecr_client(region)
    if repos:
        for i_repo in repos:
            images = ecr.describe_images(repositoryName=i_repo)["imageDetails"]
            for i in sorted(images, key=lambda d: d["imagePushedAt"]):
                images_tags = "/".join(i.get("imageTags", [""]))
                image_size = round(i["imageSizeInBytes"] / (1024 * 1024), 2)
                if images_tags:
                    print(
                        "* {imageDigest} {registryId}.dkr.ecr.{region}.amazonaws.com/{repositoryName}:{images_tags} ({image_size}Mb) - {imagePushedAt} ".format(
                            images_tags=images_tags,
                            image_size=image_size,
                            region=region,
                            **i,
                        )
                    )
    else:
        repos = ecr.describe_repositories()
        for i_repo in sorted(repos["repositories"], key=lambda d: d["repositoryUri"]):
            print(f"* {i_repo['repositoryUri']}")


@click.command(name="ecr.login")
@click.argument("cluster")
@click.option("--region", default=None)
def ecr_login(cluster, region):
    load_config()
    cluster = Cluster.get_cluster(cluster)
    region = region or cluster.regions[0]

    click.echo(
        f"aws ecr --profile=mi-shared get-login-password --region {region} | docker login --username AWS --password-stdin {cluster.aws_id}.dkr.ecr.{region}.amazonaws.com"
    )


@click.command(name="rds_snapshot.list")
@click.argument("cluster")
@click.option("--region", default=None)
def rds_snapshot_list(cluster, region):
    load_config()
    cluster = Cluster.get_cluster(cluster)
    region = region or cluster.regions[0]

    rds = cluster.client("rds", region=region)
    snapshots = rds.describe_db_snapshots(SnapshotType="automated")["DBSnapshots"]
    for i in snapshots:
        print("*", i)


@click.command(name="vpc.details")
@click.argument("cluster")
@click.option("--region", default=None)
def vpc_details(cluster, region):
    import json

    load_config()
    cluster = Cluster.get_cluster(cluster)
    region = region or cluster.regions[0]

    ec2 = cluster.ec2_resource(region=region)
    result = {}
    for i_vpc in ec2.vpcs.all():
        subnets = sorted(i_vpc.subnets.all(), key=lambda x: x.availability_zone)
        result["vpc_id"] = i_vpc.id
        # result["public_subnets"] = {}
        # result["private_subnets"] = {}
        # result["private_route_table_ids"] = {}
        # result["azs"] = {}
        result["public_subnets"] = [j.id for j in subnets if j.map_public_ip_on_launch]
        result["private_subnets"] = [
            j.id for j in subnets if not j.map_public_ip_on_launch
        ]
        result["private_route_table_ids"] = [
            j.id
            for j in i_vpc.route_tables.all()
            if j.associations_attribute[0].get("SubnetId") in result["private_subnets"]
        ]
        result["azs"] = list({j.availability_zone for j in subnets})

    print(json.dumps(result))


@click.command(name="ecs.status")
@click.argument("cluster")
@click.option("--region", default=None)
def ecs_status(cluster, region):
    load_config()
    cluster = Cluster.get_cluster(cluster)
    region = region or cluster.regions[0]

    for i_ecs_cluster in EcsCluster.list(cluster, region):
        click.echo(f"* {i_ecs_cluster.name}")
        for i_ecs_service in i_ecs_cluster.list_services():
            click.echo(f"  * {i_ecs_service.name}")


@click.command(name="ecs.deploy")
@click.argument("cluster")
@click.argument("service")
@click.option("--region", default=None)
def ecs_deploy(cluster, service, region):
    load_config()
    cluster = Cluster.get_cluster(cluster)
    region = region or cluster.regions[0]

    for i_ecs_cluster in EcsCluster.list(cluster, region):
        click.echo(f"* {i_ecs_cluster.name}")
        for i_ecs_service in i_ecs_cluster.list_services():
            click.echo(f"  * {i_ecs_service.name}")


@click.command(name="sso.autologin")
@click.argument("sso_url")
def sso_autologin(sso_url: str) -> None:
    """
    WIP: Automate AWS SSO login using the command line.

    # https://device.sso.ca-central-1.amazonaws.com/?user_code=KRGH-DGNR
    """
    click.echo(f"sso.autologin: {sso_url}")


#     from selenium import webdriver
#
#     # Initialize Selenium WebDriver (e.g., Chrome)
#     driver = webdriver.Chrome()
#
#     # Navigate to AWS SSO login page
#     driver.get("https://your-aws-sso-login-url")
#
#     # Input SSO token and submit
#     sso_token = "your-sso-token-here"
#     driver.find_element_by_id("ssoToken").send_keys(sso_token)
#     driver.find_element_by_id("signInSubmit").click()
#
#     # Continue with your automation tasks
#     # ...
