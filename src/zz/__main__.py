import click


@click.group()
def main():
    pass


@main.group()
def aws():
    pass


@aws.command()
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


@aws.command()
def applications():
    """
    List registered AWS profiles.
    """
    click.echo("""
  deployment   aws_profile  newrelic   sentry
* tier1-dev    mi-dev       518442355  tier1-dev
* tier1-stage  mi-stage     544578180  moto-stage
* tier1-prod   tier1        516056459  t1-moto-prod
""")
    pass


@aws.command("ec2.list")
def ec2_list():
    pass


@aws.command("ec2.shell")
def ec2_shell():
    pass


@aws.command("ec2.start")
def ec2_start():
    pass


@aws.command("ec2.stop")
def ec2_stop():
    pass


if __name__ == '__main__':
    main()
