terraform {
  backend "s3" {
    bucket = "qtrees-terraform"
    key    = "tfstate"
    region = "eu-central-1"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.27"
    }
  }

  required_version = ">= 0.14.9"
}

provider "aws" {
  region  = "eu-central-1"
}

data "aws_availability_zones" "available" {}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "2.77.0"

  name = "${var.project_name}-vpc"
  cidr = "10.0.0.0/16"
  azs  = data.aws_availability_zones.available.names

  #private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
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
  #subnet_ids = module.vpc.private_subnets
  subnet_ids = module.vpc.public_subnets

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}

resource "aws_db_instance" "qtrees" {
  identifier                      = "${var.project_name}-iac-rds"
  instance_class                  = "db.t3.medium"
  allocated_storage               = 20
  max_allocated_storage           = 100
  storage_type                    = "gp3"
  engine                          = "postgres"
  engine_version                  = "14.7"
  name                            = var.project_name

  # Added because of error InvalidParameterCombination:
  # You can't specify IOPS or storage throughput for engine postgres and a storage size less than 400.
  #iops                            = 3000
  username                        = "postgres"
  password                        = var.POSTGRES_PASSWD
  skip_final_snapshot             = true
  performance_insights_enabled    = true
  performance_insights_kms_key_id = null # use default key for region

  # is this needed?
  publicly_accessible = true

  db_subnet_group_name   = aws_db_subnet_group.qtrees.name
  vpc_security_group_ids = [aws_security_group.qtrees_db_sg.id]

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
    Restricted = var.restricted
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
    cidr_blocks = ["0.0.0.0/0"]
    #security_groups = [aws_security_group.qtrees_lb_sg.id]
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

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    # source IP: can be restricted to special IP
    cidr_blocks = ["0.0.0.0/0"]
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

resource "aws_key_pair" "qtrees" {
  key_name   = "${var.project_name}-key_pair"
  public_key = var.pub_key
  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}

resource "aws_instance" "qtrees" {
  # AMD Ubuntu
  ami           = "ami-065deacbcaac64cf2"
  instance_type = "t2.medium"

  root_block_device {
    volume_size = 40
  }

  # public ip needed to ssh into this instance
  associate_public_ip_address = true
  subnet_id                   = module.vpc.public_subnets[0]
  security_groups             = [aws_security_group.qtrees_ec2_sg.id]

  key_name = aws_key_pair.qtrees.key_name

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
    Restricted = var.restricted
  }
}

# use this for generating a elastic ip on creation
//resource "aws_eip" "qtrees" {
//  instance = aws_instance.qtrees.id
//
//  tags = {
//    Name = "${var.project_name}-iac-${var.qtrees_version}"
//  }
//}

# re-use existing elastic ip (if set)
data "aws_eip" "qtrees" {
//  count = try(var.ELASTIC_IP_EC2 == "" ? 0 : 1, 0)
  public_ip = "${var.ELASTIC_IP_EC2}"
}

resource "aws_eip_association" "eip_assoc" {
  instance_id   = aws_instance.qtrees.id
  allocation_id = data.aws_eip.qtrees.id
}

# Export Terraform variable values to an Ansible var_file
resource "local_file" "tf_ansible_vars_file" {
  content  = <<-DOC
    [qtrees_server:vars]
    ansible_ssh_private_key_file=${var.private_key}
    [qtrees_server]
    ubuntu@${data.aws_eip.qtrees.public_dns}
    DOC
  filename = "./ansible/hosts"
}

resource "local_file" "setup_env_file" {
  content  = <<-DOC
    export QTREES_VERSION=${var.project_name}
    export GIS_PASSWD=${var.GIS_PASSWD}
    export AUTH_PASSWD=${var.AUTH_PASSWD}
    export JWT_SECRET=${var.JWT_SECRET}
    export POSTGRES_PASSWD=${var.POSTGRES_PASSWD}
    export DB_ADMIN_PASSWD=${var.DB_ADMIN_PASSWD}
    export DB_USER_PASSWD=${var.DB_USER_PASSWD}
    export UI_USER_PASSWD=${var.UI_USER_PASSWD}
    export DB_QTREES=${aws_db_instance.qtrees.address}
    export DB_GDK=${var.DB_GDK}
    export GDK_PASSWD=${var.GDK_PASSWD}
    export SOLARANYWHERE_API_KEY='${var.SOLARANYWHERE_API_KEY}'
    export CMD_GIS_ADMIN="GRANT rds_superuser TO gis_admin;" # with rds !
    DOC
  filename = "./tf_output/setup_environment.sh"
}

resource "local_file" "ssh_file" {
  content  = <<-DOC
    ssh -i "~/.ssh/qtrees.pem" ubuntu@${data.aws_eip.qtrees.public_dns}
    DOC
  filename = "./tf_output/ssh_to_ec2.sh"
}

# TODO can only be executed from ec2 instance. does this make sense to create this file?
resource "local_file" "connect_to_db" {
  content  = <<-DOC
    PGPASSWORD=${var.POSTGRES_PASSWD} psql --host=${aws_db_instance.qtrees.address} --port=5432 --username=postgres --dbname=${var.project_name}
    DOC
  filename = "./tf_output/connect_to_db.sh"
}
