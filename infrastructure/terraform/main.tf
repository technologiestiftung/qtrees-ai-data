terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.27"
    }
  }

  required_version = ">= 0.14.9"
}

provider "aws" {
  region  = var.region
}

# TODO create ECR repository
data "aws_availability_zones" "available" {}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "2.77.0"

  name = "${var.project_name}-vpc"
  cidr = "10.0.0.0/16"
  azs  = data.aws_availability_zones.available.names

  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.8.0/24", "10.0.5.0/24"]

  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}

resource "aws_db_subnet_group" "qtrees" {
  # identifier
  name = "${var.project_name}-subnet"
  # just use this subnet for now
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}

resource "aws_db_instance" "qtrees" {
  identifier        = "${var.project_name}-iac-rds"
  instance_class    = "db.t3.micro"
  allocated_storage = 5
  engine            = "postgres"
  name              = var.project_name
  username          = "postgres"
  password            = var.POSTGRES_PASSWD
  skip_final_snapshot = true

  # is this needed?
  publicly_accessible = true

  db_subnet_group_name   = aws_db_subnet_group.qtrees.name
  vpc_security_group_ids = [aws_security_group.qtrees_db_sg.id]

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}

resource "aws_security_group" "qtrees_ec2_sg" {
  name        = "${var.project_name}_ec2_sg"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "SSH rule"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    # source IP: can be restricted to special IP
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "HTTP"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    # source IP: can be restricted to special IP
    # security_groups = [aws_security_group.qtrees_lb_sg.id]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}


resource "aws_security_group" "qtrees_db_sg" {
  name   = "${var.project_name}_db_sg"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    # source IP: can be restricted to special IP
    security_groups = [aws_security_group.qtrees_ec2_sg.id]
  }

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}

module "qtrees_ecs" {
  source = "./qtrees_ecs" 
}