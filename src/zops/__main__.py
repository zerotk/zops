import click

import zops.aws.cli_commands as aws_commands


@click.group()
@click.pass_context
def main(ctx):
    ctx.color = True
    pass


@main.group()
def aws():
    pass


aws.add_command(aws_commands.ami_build)
aws.add_command(aws_commands.ami_deregister)
aws.add_command(aws_commands.ami_list)
aws.add_command(aws_commands.asg_instance_refresh, "asg.instance-refresh")
aws.add_command(aws_commands.asg_list)
aws.add_command(aws_commands.asg_update)
aws.add_command(aws_commands.aws_configure_profile, "configure-profile")
aws.add_command(aws_commands.deployments_list, "deployments.list")
aws.add_command(aws_commands.ec2_list)
aws.add_command(aws_commands.ec2_shell)
aws.add_command(aws_commands.ec2_start, "ec2.start")
aws.add_command(aws_commands.ecr_list)
aws.add_command(aws_commands.ecr_login)
aws.add_command(aws_commands.ecs_status)
aws.add_command(aws_commands.params_del)
aws.add_command(aws_commands.params_get)
aws.add_command(aws_commands.params_list)
aws.add_command(aws_commands.params_put)
aws.add_command(aws_commands.params_set)
aws.add_command(aws_commands.rds_snapshot_list)
aws.add_command(aws_commands.resources_clean)
aws.add_command(aws_commands.resources_clear_default_vps)
aws.add_command(aws_commands.vpc_details)
aws.add_command(aws_commands.ecs_deploy)
aws.add_command(aws_commands.sso_autologin)

if __name__ == "__main__":
    main()
