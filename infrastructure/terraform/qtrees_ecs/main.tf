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
    subnets = var.subnets
    security_groups = var.security_groups
    assign_public_ip = true
  }

  # TODO fix IP address
  #   load_balancer {
  #     target_group_arn = "${var.target_group_arn}"
  #     container_name   = "${var.project_name}"
  #     container_port   = "${var.container_port}"
  #   }
}

resource "aws_ecs_task_definition" "scheduled_task" {
  family = "${var.project_name}-scheduled_task"
  # container_definitions = "${data.template_file.task_definition.rendered}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn = "arn:aws:iam::${var.AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole"
  container_definitions = jsonencode([
    {
      name = "${var.project_name}-container1"
      # TODO handle exec error
      # image = "${var.AWS_ACCOUNT_ID}.dkr.ecr.eu-central-1.amazonaws.com/test_repo:latest"
      image = "python:3.8-alpine"
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
      # TODO need credentials or role being able to pull image from this repo
      # TODO handle exec error with test_repo image container
      # image = "${var.AWS_ACCOUNT_ID}.dkr.ecr.eu-central-1.amazonaws.com/test_repo:latest"
      image = "python:3.8-alpine"
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
  # TODO remove hardcoded aws account 
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

  # tags = {
  #   Name = "${var.project_name}-iac-${var.qtrees_version}"
  # }
}

resource "aws_cloudwatch_log_group" "postgrest_service" {
  name = "${var.project_name}-postgrest-logs"

  # tags = {
  #   Name = "${var.project_name}-iac-${var.qtrees_version}"
  # }
}