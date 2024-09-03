# Image details
variable "ami_name" { type = string }
variable "ami_regions" { default=[] }
variable "ami_users" { default=[] }
variable "overwrite" { default = false }

# Base image details
variable "baseimage_ami_name" { type = string }
variable "baseimage_ami_owners" { type = list(string) }

# Build infrastructure
variable "aws_profile" { default = null }
variable "aws_region" { default = "ca-central-1" }
variable "aws_role_arn" { default = "arn:aws:iam::050946403637:role/mi-shared-deployer2" }
variable "instance_type" { default = "t3.large" }

# Extra resources
variable "provisioner_files" { default = {} }
variable "provisioner_script" { type = string }
variable "provisioner_env" { default = [] }


data "amazon-ami" "source_ami" {
  profile = var.aws_profile
  region  = var.aws_region
  assume_role {
    role_arn = var.aws_role_arn
  }

  filters = {
    architecture        = "x86_64"
    name                = var.baseimage_ami_name
    root-device-type    = "ebs"
    virtualization-type = "hvm"
  }
  most_recent = true
  owners      = var.baseimage_ami_owners
}

source "amazon-ebs" "image" {
  profile = var.aws_profile
  region  = var.aws_region
  assume_role {
    role_arn = var.aws_role_arn
  }

  # mi-shared
  vpc_id    = "vpc-02e0568797d475abf"  # aws-controltower-VPC
  subnet_id = "subnet-02075514276f903f5"  # aws-controltower-PublicSubnet1

  source_ami              = data.amazon-ami.source_ami.id
  ami_name                = var.ami_name
  ami_regions             = var.ami_regions
  ami_users               = var.ami_users
  ami_virtualization_type = "hvm"

  associate_public_ip_address               = true
  temporary_security_group_source_public_ip = true

  instance_type = var.instance_type
  ssh_username  = "admin"
  ssh_timeout   = "5m"

  force_deregister      = var.overwrite
  force_delete_snapshot = var.overwrite

# TODO: Configure main volume
#   launch_block_device_mappings {
#     device_name = "/dev/sda1"
#     volume_size = 10
#     volume_type = "gp3"
#     iops = 3000
#     throughput = 125
#     delete_on_termination = true
#   }

# TODO: Configure EBS encryption
#   encrypt_boot = true
#   kms_key_id   = "alias/mi/ebs"
#   region_kms_key_ids = {
#     for i in var.ami_regions :
#     i => "alias/mi/ebs"
#   }

# TODO: tags
  # tags = {
  #   Name    = var.image_name
  #   Version = var.version
  # }
}

build {
  sources = ["source.amazon-ebs.image"]
  dynamic provisioner {
    labels = ["file"]
    for_each = var.provisioner_files
    content {
      source      = "${provisioner.value}"
      destination = "/tmp/${provisioner.key}"
    }
  }
  provisioner "shell" {
    environment_vars = var.provisioner_env
    script           = var.provisioner_script
  }
}

packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = "~> 1"
    }
  }
}