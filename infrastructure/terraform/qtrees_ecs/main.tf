# locals {
#   # this is the namespace for the ssm param system
#   # used by the app to fetch params at startup, see scripts/param.py
#   app_name = "${var.vpc_name}-${var.app_name}"
# }

# resource "aws_ecs_service" "postgrest_service" {
#   name                = "${var.project_name}"
# #   cluster             = "${var.cluster}"
#   desired_count       = "1"
#   task_definition     = "${aws_ecs_task_definition.app.arn}"
#   scheduling_strategy = "REPLICA"

#   # 50 percent must be healthy during deploys
#   deployment_minimum_healthy_percent = 50
#   deployment_maximum_percent         = 100

# # TODO fix IP address
# #   load_balancer {
# #     target_group_arn = "${var.target_group_arn}"
# #     container_name   = "${var.project_name}"
# #     container_port   = "${var.container_port}"
# #   }
# }

# scheduled tasks
# https://docs.aws.amazon.com/AmazonECS/latest/developerguide/scheduled_tasks.html  
# https://vthub.medium.com/running-ecs-fargate-tasks-on-a-schedule-fd1ca428e669

# ecs task file
# https://github.com/navapbc/tf-ecs-example/tree/master/templates/basic-app/ecs-tasks
# data "template_file" "task_definition" {
#   template = "${file("${path.module}/task_definitions/postgrest_task.json")}"

#   vars {
#     docker_image_url = "${aws_ecr_repository.qtrees.repository_url}"
#     container_name   = "postgrest_service"
#     aws_region       = "${var.region}"
#     ssm_path         = "/${var.vpc_name}/${var.app_name}"
#     container_port   = "${var.container_port}"
#     health_check     = "${var.health_check}"
#   }
# }

# TODO take a look at logging config https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_cluster
resource "aws_ecs_cluster" "qtrees" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}


resource "aws_ecs_task_definition" "postgrest_task" {
  family = "${var.project_name}-postgrest_task"
  # container_definitions = "${data.template_file.task_definition.rendered}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512

  # TODO add database name and user as variables
  # TODO put this in json and map variables
  container_definitions = <<EOF
  [
    {
      "name": "${var.project_name}-postgrest",
      "image": "registry.hub.docker.com/postgrest/postgrest",
      "cpu": 0,
      "portMappings": [
        {
          "containerPort": 3000,
          "hostPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
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
      "essential": true
    }
  ]
  EOF

  # TODO put this into container definitions and check if logging works. need aws aws_iam_role for this to work
            # "logConfiguration": {
            #     "logDriver": "awslogs",
            #     "options": {
            #         "awslogs-group": "/fargate/service/postgrest",
            #         "awslogs-region": "eu-central-1",
            #         "awslogs-stream-prefix": "fargate"
            #     }
            # }

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

  # TODO assign the vpc configs
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
  execution_role_arn = "arn:aws:iam::257772343150:role/ecsTaskExecutionRole"
  container_definitions = jsonencode([
    {
      name = "${var.project_name}-scheduled"
      image = "python:3.8-alpine"
      # image = "257772343150.dkr.ecr.eu-central-1.amazonaws.com/test_repo"
      command = ["python", "-c", "print('Hello, World!')"]
      # logConfiguration =  {
      #     logDriver = "awslogs",
      #     options =  {
      #         "awslogs-group": "/fargate/scheduled_task",
      #         "awslogs-region": "eu-central-1",
      #         "awslogs-stream-prefix": "fargate"
      #     }
      # }
    }
  ])
}

resource "aws_cloudwatch_event_rule" "qtrees" {
  name = "${var.project_name}-schedule"
  schedule_expression = "rate(1 minute)"
}

resource "aws_cloudwatch_event_target" "qtrees" {
  rule      = aws_cloudwatch_event_rule.qtrees.name
  target_id = "${var.project_name}-target"
  arn       = aws_ecs_cluster.qtrees.arn
  # TODO remove hardcoded role
  role_arn = "arn:aws:iam::257772343150:role/ecsTaskExecutionRole"
  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.scheduled_task.arn
    launch_type = "FARGATE"
    network_configuration {
      subnets = var.subnets
      # TODO do we need another group here?
      security_groups = var.security_groups
    }
  }
}