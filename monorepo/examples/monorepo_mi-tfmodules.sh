#!/bin/bash

set -e

source ./monorepo.lib.bash

monorepo__main \
  mi-infra-tfmodules  \
  git@github.com:tdr-autosync/mi-tfmodule-ami_build,tfmodules/ami_build  \
  git@github.com:tdr-autosync/mi-tfmodule-auto_deploy#main,tfmodules/auto_deploy  \
  git@github.com:tdr-autosync/mi-tfmodule-autoscaling_group,tfmodules/autoscaling_group  \
  git@github.com:tdr-autosync/mi-tfmodule-cloudwatch,tfmodules/cloudwatch  \
  git@github.com:tdr-autosync/mi-tfmodule-cloudwatch_agent_conf,tfmodules/cloudwatch_agent_conf  \
  git@github.com:tdr-autosync/mi-tfmodule-cloudwatch_alarms#main,tfmodules/cloudwatch_alarms  \
  git@github.com:tdr-autosync/mi-tfmodule-cloudwatch_slack_notifications,tfmodules/cloudwatch_slack_notifications  \
  git@github.com:tdr-autosync/mi-tfmodule-database,tfmodules/database  \
  git@github.com:tdr-autosync/mi-tfmodule-deployment,tfmodules/deployment  \
  git@github.com:tdr-autosync/mi-tfmodule-ec2_alerts,tfmodules/ec2_alerts  \
  git@github.com:tdr-autosync/mi-tfmodule-ecs_cluster#main,tfmodules/ecs_cluster  \
  git@github.com:tdr-autosync/mi-tfmodule-ecs_service#main,tfmodules/ecs_service  \
  git@github.com:tdr-autosync/mi-tfmodule-ecs_taskdef#main,tfmodules/ecs_taskdef  \
  git@github.com:tdr-autosync/mi-tfmodule-efs#main,tfmodules/efs  \
  git@github.com:tdr-autosync/mi-tfmodule-flower,tfmodules/flower  \
  git@github.com:tdr-autosync/mi-tfmodule-ftp,tfmodules/ftp  \
  git@github.com:tdr-autosync/mi-tfmodule-iam#main,tfmodules/iam  \
  git@github.com:tdr-autosync/mi-tfmodule-iam_access_role,tfmodules/iam_access_role  \
  git@github.com:tdr-autosync/mi-tfmodule-iam_shell_role,tfmodules/iam_shell_role  \
  git@github.com:tdr-autosync/mi-tfmodule-iam_terraform_role,tfmodules/iam_terraform_role  \
  git@github.com:tdr-autosync/mi-tfmodule-instance,tfmodules/instance  \
  git@github.com:tdr-autosync/mi-tfmodule-load_balancer,tfmodules/load_balancer  \
  git@github.com:tdr-autosync/mi-tfmodule-mi_iam_roles,tfmodules/mi_iam_roles  \
  git@github.com:tdr-autosync/mi-tfmodule-newrelic_load_balancer_logs#main,tfmodules/newrelic_load_balancer_logs  \
  git@github.com:tdr-autosync/mi-tfmodule-newrelic_stream,tfmodules/newrelic_stream  \
  git@github.com:tdr-autosync/mi-tfmodule-redash,tfmodules/redash  \
  git@github.com:tdr-autosync/mi-tfmodule-redis,tfmodules/redis  \
  git@github.com:tdr-autosync/mi-tfmodule-s3_bucket,tfmodules/s3_bucket  \
  git@github.com:tdr-autosync/mi-tfmodule-ssm_user#main,tfmodules/ssm_user  \
  git@github.com:tdr-autosync/mi-tfmodule-static_website,tfmodules/static_website

# BRANCHES:
# * t3can-cluster#infra_1635
# * t3can-cluster#infra_2068
# * tier1-cluster#infra_2046
