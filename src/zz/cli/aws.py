import click


@click.group(name="aws")
def main():
    pass


@main.command("c")
def cloud():
    """
    List registered cloud accounts profiles.
    """
    # from zz.services.aws_provider import AwsProvider
    import boto3
    import botocore

    for i, i_profile in enumerate(boto3.session.Session().available_profiles):
        try:
            s = boto3.session.Session(profile_name=i_profile)
            identity = s.client("sts").get_caller_identity()
            account_id = identity["Account"]
        except botocore.exceptions.NoCredentialsError:
            account_id = "?"
        print(i_profile, account_id)
        if i > 3:
            break


@main.command("d")
def deployments():
    """
    List registered deployments.
    """
    click.echo(
        """
  deployment   aws_profile  newrelic   sentry
* tier1-dev    mi-dev       518442355  tier1-dev
* tier1-stage  mi-stage     544578180  moto-stage
* tier1-prod   tier1        516056459  t1-moto-prod
"""
    )
    pass


@main.command("ec2.list")
def ec2_list():
    """
    List ec2 instances.
    """
    pass


@main.command("ec2.shell")
def ec2_shell():
    """
    Shell into an ec2 instance.
    """
    pass


@main.command("ec2.start")
def ec2_start():
    """
    Starts a stopped ec2 instance.
    """
    pass


@main.command("ec2.stop")
def ec2_stop():
    """
    Stops a running ec2 instance.
    """
    pass


@main.command("params.list")
def params_list():
    """
    List SSM Parameters.
    """
    pass


@main.command("params.get")
def params_get():
    """
    Get the value of one or more SSM parameters.
    """
    pass


@main.command("params.set")
def params_set():
    """
    Sets the value of one or more SSM Parameters.
    """
    pass


@main.command("ami.list")
def ami_list():
    """
    List AMI images.
    """
    pass


@main.command("ami.deregister")
def ami_build():
    """
    Deregister (delete) an AMI image.
    """
    pass


@main.command("asg.list")
def asg_list():
    """
    List ASGs (auto scaling groups).
    """
    pass


@main.command("asg.update")
def asg_update():
    """
    Updates an ASG (auto scaling group).
    """
    pass
