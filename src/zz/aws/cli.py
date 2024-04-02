import click

import zops.aws.cli_commands as commands


@click.group(name="aws")
def main():
    """
    AWS-related commands (including ec2, aws, asg).
    """

main.add_command(commands.ami_build)
main.add_command(commands.ami_deregister)
main.add_command(commands.ami_list)
main.add_command(commands.asg_instance_refresh, "asg.instance-refresh")
main.add_command(commands.asg_list)
main.add_command(commands.asg_update)
main.add_command(commands.aws_configure_profile, "configure-profile")
main.add_command(commands.deployments_list, "deployments.list")
main.add_command(commands.ec2_list)
main.add_command(commands.ec2_shell)
main.add_command(commands.ec2_start, "ec2.start")
main.add_command(commands.ecr_list)
main.add_command(commands.ecr_login)
main.add_command(commands.ecs_status)
main.add_command(commands.params_del)
main.add_command(commands.params_get)
main.add_command(commands.params_list)
main.add_command(commands.params_put)
main.add_command(commands.params_set)
main.add_command(commands.rds_snapshot_list)
main.add_command(commands.resources_clean)
main.add_command(commands.resources_clear_default_vps)
main.add_command(commands.vpc_details)
main.add_command(commands.ecs_deploy)
