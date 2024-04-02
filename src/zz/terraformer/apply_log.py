import json
from logging import getLogger
from typing import Any, Dict, List

logger = getLogger(__name__)


RESOURCE_TYPES = ["apply_start", "apply_progress", "apply_complete", "apply_errored", "planned_change"]

RESOURCE_STATUSES = {
    "planned_change": "planned",
    "apply_start": "starting",
    "apply_progress": "in_progress",
    "apply_complete": "finished",
    "apply_errored": "failed",
}


class TerraformApplyLog:
    resources: Dict[str, Any] = {}
    errors: List[str] = []
    changes: Dict[str, Any] = {}
    terraform_version: str = ""
    outputs: Dict[str, Any] = {}

    def add_lines(self, log_lines: str) -> None:
        for log_line in log_lines.split("\n"):
            if len(log_line) < 1:
                continue
            self.add_line(log_line)

    def add_line(self, log_line: str) -> None:
        log: Dict[str, Any]
        try:
            log = json.loads(log_line)
        except json.decoder.JSONDecodeError:
            # TODO - we should try to decode this in some other way
            logger.warning(f"Apply log includes line of invalid json")
            return

        if log["type"].startswith("refresh_"):
            return

        # apply_start: {"@level":"info","@message":"module.vpc.module.nat_gateway[0].aws_route.route_to_nat[1]: Destroying... [id=r-rtb-06df695578f26432f1080289494]","@module":"terraform.ui","@timestamp":"2022-08-11T10:17:40.692416-05:00","hook":{"resource":{"addr":"module.vpc.module.nat_gateway[0].aws_route.route_to_nat[1]","module":"module.vpc.module.nat_gateway[0]","resource":"aws_route.route_to_nat[1]","implied_provider":"aws","resource_type":"aws_route","resource_name":"route_to_nat","resource_key":1},"action":"delete","id_key":"id","id_value":"r-rtb-06df695578f26432f1080289494"},"type":"apply_start"}
        # apply_progress: {"@level":"info","@message":"module.vpc.aws_internet_gateway_attachment.main: Still destroying... [10s elapsed]","@module":"terraform.ui","@timestamp":"2022-08-11T10:17:50.696783-05:00","hook":{"resource":{"addr":"module.vpc.aws_internet_gateway_attachment.main","module":"module.vpc","resource":"aws_internet_gateway_attachment.main","implied_provider":"aws","resource_type":"aws_internet_gateway_attachment","resource_name":"main","resource_key":null},"action":"delete","elapsed_seconds":10},"type":"apply_progress"}
        # apply_progress: {"@level":"info","@message":"module.vpc.module.nat_gateway[0].aws_nat_gateway.main[0]: Still creating... [1m40s elapsed]","@module":"terraform.ui","@timestamp":"2022-08-11T09:56:00.104645-05:00","hook":{"resource":{"addr":"module.vpc.module.nat_gateway[0].aws_nat_gateway.main[0]","module":"module.vpc.module.nat_gateway[0]","resource":"aws_nat_gateway.main[0]","implied_provider":"aws","resource_type":"aws_nat_gateway","resource_name":"main","resource_key":0},"action":"create","elapsed_seconds":100},"type":"apply_progress"}
        # apply_complete: {"@level":"info","@message":"module.vpc.module.nat_gateway[0].aws_route.route_to_nat[2]: Destruction complete after 0s","@module":"terraform.ui","@timestamp":"2022-08-11T10:17:41.454174-05:00","hook":{"resource":{"addr":"module.vpc.module.nat_gateway[0].aws_route.route_to_nat[2]","module":"module.vpc.module.nat_gateway[0]","resource":"aws_route.route_to_nat[2]","implied_provider":"aws","resource_type":"aws_route","resource_name":"route_to_nat","resource_key":2},"action":"delete","elapsed_seconds":0},"type":"apply_complete"}
        # planned_change: {"@level":"info","@message":"module.vpc.module.availability_zones[2].aws_subnet.public: Plan to create","@module":"terraform.ui","@timestamp":"2022-08-11T09:54:03.688924-05:00","change":{"resource":{"addr":"module.vpc.module.availability_zones[2].aws_subnet.public","module":"module.vpc.module.availability_zones[2]","resource":"aws_subnet.public","implied_provider":"aws","resource_type":"aws_subnet","resource_name":"public","resource_key":null},"action":"create"},"type":"planned_change"}
        if log["type"] in RESOURCE_TYPES:
            self.process_resource(log)
            return

        # {"@level":"info","@message":"Apply complete! Resources: 32 added, 0 changed, 0 destroyed.","@module":"terraform.ui","@timestamp":"2022-08-11T09:56:06.970120-05:00","changes":{"add":32,"change":0,"remove":0,"operation":"apply"},"type":"change_summary"}
        if log["type"] == "change_summary":
            self.changes = log["changes"]
            return

        # {"@level":"info","@message":"Terraform 1.1.7","@module":"terraform.ui","@timestamp":"2022-08-11T09:58:58.654191-05:00","terraform":"1.1.7","type":"version","ui":"1.0"}
        if log["type"] == "version":
            self.terraform_version = log["ui"]
            return

        # {"@level":"info","@message":"Outputs: 1","@module":"terraform.ui","@timestamp":"2022-08-11T09:59:00.389242-05:00","outputs":{"vpc":{"sensitive":false,"type":["object",{"arn":"string","assign_generated_ipv6_cidr_block":"bool","cidr_block":"string","default_network_acl_id":"string","default_route_table_id":"string","default_security_group_id":"string","dhcp_options_id":"string","enable_classiclink":"bool","enable_classiclink_dns_support":"bool","enable_dns_hostnames":"bool","enable_dns_support":"bool","id":"string","instance_tenancy":"string","ipv4_ipam_pool_id":"string","ipv4_netmask_length":"number","ipv6_association_id":"string","ipv6_cidr_block":"string","ipv6_cidr_block_network_border_group":"string","ipv6_ipam_pool_id":"string","ipv6_netmask_length":"number","main_route_table_id":"string","owner_id":"string","tags":["map","string"],"tags_all":["map","string"]}],"value":{"arn":"arn:aws:ec2:us-west-2:755842654594:vpc/vpc-010f9dfb4129daaca","assign_generated_ipv6_cidr_block":false,"cidr_block":"10.246.0.0/16","default_network_acl_id":"acl-0a5dd0254c60c41b0","default_route_table_id":"rtb-0b774b6dc44ee4bc8","default_security_group_id":"sg-0401f1cc7fdb04283","dhcp_options_id":"dopt-0e7128608c809b67b","enable_classiclink":false,"enable_classiclink_dns_support":false,"enable_dns_hostnames":true,"enable_dns_support":true,"id":"vpc-010f9dfb4129daaca","instance_tenancy":"default","ipv4_ipam_pool_id":null,"ipv4_netmask_length":null,"ipv6_association_id":"","ipv6_cidr_block":"","ipv6_cidr_block_network_border_group":"","ipv6_ipam_pool_id":"","ipv6_netmask_length":0,"main_route_table_id":"rtb-0b774b6dc44ee4bc8","owner_id":"755842654594","tags":{"Name":"test-246"},"tags_all":{"Name":"test-246"}}}},"type":"outputs"}
        if log["type"] == "outputs":
            self.outputs = log["outputs"]
            return

        # {"@level":"error","@message":"Error: deleting Security Group (sg-0fb61810ade27ddca): DependencyViolation: resource sg-0fb61810ade27ddca has a dependent object\n\tstatus code: 400, request id: 0d6344b6-8338-466f-a90c-2a04c1e3b043","@module":"terraform.ui","@timestamp":"2022-09-12T19:51:17.376115Z","diagnostic":{"severity":"error","summary":"deleting Security Group (sg-0fb61810ade27ddca): DependencyViolation: resource sg-0fb61810ade27ddca has a dependent object\n\tstatus code: 400, request id: 0d6344b6-8338-466f-a90c-2a04c1e3b043","detail":""},"type":"diagnostic"}
        if log["type"] == "diagnostic":
            if log["diagnostic"]["severity"] == "error":
                self.errors.append(log["diagnostic"]["summary"])
            return

        logger.warning(f"Apply log includes unknown type: {log['type']}")

    def process_resource(self, resource_log) -> None:
        if resource_log["type"] not in RESOURCE_TYPES:
            raise ValueError(f"Unexpected log type passed: {resource_log['type']}")

        resource_key = "hook" if resource_log["type"].startswith("apply_") else "change"
        self.resources[resource_log[resource_key]["resource"]["addr"]] = {
            **resource_log[resource_key]["resource"],
            "action": resource_log[resource_key]["action"],
            "status": RESOURCE_STATUSES[resource_log["type"]],
        }
