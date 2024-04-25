import click


@click.group(name="aws")
def main():
    pass


@main.command("c")
def cloud():
    """
    List registered cloud accounts profiles.
    """
    click.echo("""
* mi-stage 123456789000 ca-central-1
* tier3    150000000000 ca-central-1
* internal 299378319612 ca-central-1/us-east-2
* tier1    624664959560 ca-central-1
""")
    pass


@main.command("d")
def deployments():
    """
    List registered deployments.
    """
    click.echo("""
  deployment   aws_profile  newrelic   sentry
* tier1-dev    mi-dev       518442355  tier1-dev
* tier1-stage  mi-stage     544578180  moto-stage
* tier1-prod   tier1        516056459  t1-moto-prod
""")
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
