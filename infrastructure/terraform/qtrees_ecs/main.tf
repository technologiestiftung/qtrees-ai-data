resource "aws_ecs_cluster" "qtrees" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "postgrest_task" {
  family = "${var.project_name}-postgrest_task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn = "arn:aws:iam::${var.AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole"

  # TODO add database name and user as variables
  container_definitions = jsonencode([
    {
      name = "${var.project_name}-postgrest"
      image = "registry.hub.docker.com/postgrest/postgrest",
      cpu = 256,
      portMappings = [
        {
          "containerPort": 3000,
          "hostPort": 3000,
          "protocol": "tcp"
        }
      ],
      environment = [
        {
            "name": "PGRST_DB_SCHEMA",
            "value": "api"
        },
        {
            "name": "PGRST_JWT_SECRET",
            "value": "${var.jwt_secret}"
        },
        {
            "name": "PGRST_DB_MAX_ROWS",
            "value": "10"
        },
        {
            "name": "PGRST_DB_URI",
            "value": "postgresql://postgres:${var.postgres_passwd}@${var.db_instance_uri}:5432/postgres"
        },
        {
            "name": "PGRST_DB_ANON_ROLE",
            "value": "web_anon"
        }
      ],
      essential = true

      logConfiguration =  {
          logDriver = "awslogs",
          options =  {
              "awslogs-group": aws_cloudwatch_log_group.postgrest_service.name,
              "awslogs-region": "eu-central-1",
              "awslogs-stream-prefix": "postgrest"
          }
      }
    }
  ])
}

resource "aws_ecs_service" "postgrest_service" {
  name                = "${var.project_name}-postgrest-service"
  cluster             = aws_ecs_cluster.qtrees.name
  desired_count       = "1"
  task_definition     = aws_ecs_task_definition.postgrest_task.arn
  scheduling_strategy = "REPLICA"
  launch_type         = "FARGATE"
  
  # 50 percent must be healthy during deploys
  # deployment_minimum_healthy_percent = 50
  # deployment_maximum_percent         = 100

  network_configuration {
    # must be private subnets then? 
    subnets = var.subnets
    security_groups = var.security_groups
    # for whatever reason this is required when pulling image 
    assign_public_ip = true
  }
}

resource "aws_ecs_task_definition" "scheduled_task" {
  family = "${var.project_name}-scheduled_task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn = "arn:aws:iam::${var.AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole"
  container_definitions = jsonencode([
    {
      name = "${var.project_name}-container1"
      # TODO handle exec error
      image = "${var.AWS_ACCOUNT_ID}.dkr.ecr.eu-central-1.amazonaws.com/test_repo:latest"
      cpu = 30,
      # spaces in arguments lead to syntax error
      command = ["python", "-c", "print('container_to_update_database')"]
      logConfiguration =  {
          logDriver = "awslogs",
          options =  {
              "awslogs-group": aws_cloudwatch_log_group.scheduled_tasks.name,
              "awslogs-region": "eu-central-1",
              "awslogs-stream-prefix": "container1_logs"
          }
      }
    },
    {
      name = "${var.project_name}-container2"
      image = "${var.AWS_ACCOUNT_ID}.dkr.ecr.eu-central-1.amazonaws.com/test_repo:latest"
      cpu = 30,
      # spaces in arguments lead to syntax error
      command = ["python", "-c", "print('some_random_task')"]
      logConfiguration =  {
          logDriver = "awslogs",
          options =  {
              "awslogs-group": aws_cloudwatch_log_group.scheduled_tasks.name,
              "awslogs-region": "eu-central-1",
              "awslogs-stream-prefix": "container2_logs"
          }
      }
    }

  ])
}

resource "aws_cloudwatch_event_rule" "qtrees" {
  name = "${var.project_name}-schedule"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "qtrees" {
  rule      = aws_cloudwatch_event_rule.qtrees.name
  target_id = "${var.project_name}-target"
  arn       = aws_ecs_cluster.qtrees.arn
  role_arn = "arn:aws:iam::${var.AWS_ACCOUNT_ID}:role/ecsEventsRole"
  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.scheduled_task.arn
    launch_type = "FARGATE"
    network_configuration {
      subnets = var.subnets
      security_groups = var.security_groups
      assign_public_ip = true
    }
  }
}

resource "aws_cloudwatch_log_group" "scheduled_tasks" {
  name = "${var.project_name}-scheduled_tasks-logs"

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}

resource "aws_cloudwatch_log_group" "postgrest_service" {
  name = "${var.project_name}-postgrest-logs"

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}

# ============================= LOAD BALANCING
resource "aws_eip" "qtrees" {
  vpc      = true
}
resource "aws_lb" "qtrees" {
  name               = "${var.project_name}-lb"
  internal           = false
  load_balancer_type = "network"

  subnet_mapping {
    subnet_id     = var.subnets[0]
    allocation_id = aws_eip.qtrees.id
  }

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}

resource "aws_security_group" "qtrees_lb_sg" {
  name   = "${var.project_name}-lb-sg"
  vpc_id = var.vpc_id
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
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

resource "aws_lb_target_group" "qtrees_lb_tg" {
  name     = "${var.project_name}-lb-tg"
  port     = 3000
  protocol = "TCP"
  target_type = "ip"
  vpc_id   = var.vpc_id

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}

# resource "aws_lb_target_group_attachment" "target_ip" {
#   target_group_arn = aws_lb_target_group.qtrees_lb_tg.arn

#   # TODO assign private IP of postgrest_task here.
#   # for some reason this cannot be done because we cannot infer ip at build time
#   target_id        = "10.0.8.180"
#   port             = 3000
# }

resource "aws_lb_listener" "qtrees" {
  load_balancer_arn = aws_lb.qtrees.arn
  port              = "80"
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.qtrees_lb_tg.arn
  }

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}
