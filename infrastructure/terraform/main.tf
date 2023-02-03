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

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "2.77.0"

  name = "${var.project_name}-vpc"
  cidr = "10.0.0.0/16"
  azs  = ["eu-central-1a", "eu-central-1b", "eu-central-1c"]
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

resource "aws_security_group" "qtrees" {
  name        = "${var.project_name}_sg"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    # source IP: can be restricted to special IP
    cidr_blocks      = ["0.0.0.0/0"]    
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
    security_groups = [aws_security_group.qtrees.id]
  }

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}

# resource "aws_s3_bucket" "qtrees" {
#   bucket = "${var.project_name}_data"

#   tags = {
#     Name = "${var.project_name}-iac-${var.qtrees_version}"
#   }
# }

# resource "aws_ecr_repository" "qtrees" {
#   name                 = "${var.project_name}-ecr"
#   image_tag_mutability = "MUTABLE"

#   image_scanning_configuration {
#     scan_on_push = false
#   }
# }

module "qtrees_ecs" {
  source = "./qtrees_ecs" 
  project_name = var.project_name
  subnets = module.vpc.public_subnets
  security_groups = [aws_security_group.qtrees.id]
  db_instance_uri = aws_db_instance.qtrees.address
  postgres_passwd = var.POSTGRES_PASSWD
  jwt_secret = var.JWT_SECRET
  AWS_ACCOUNT_ID = var.AWS_ACCOUNT_ID
}
