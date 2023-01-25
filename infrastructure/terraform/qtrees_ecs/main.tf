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
  family                = "${var.project_name}"
  # container_definitions = "${data.template_file.task_definition.rendered}"
  network_mode          = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                   = 256
  memory                = 512

  # "image": "${aws_ecr_repository.qtrees.repository_url}:latest",
  container_definitions = <<EOF
  [
    {
      "name": "${var.project_name}-postgrest",
      "image": "registry.hub.docker.com/postgrest/postgrest",
      "portMappings": [
        {
          "containerPort": 3000,
          "hostPort": 3000
        }
      ],
      "essential": true,
      "memoryReservation": 256
    }
  ]
  EOF
}

resource "aws_ecs_service" "postgrest_service" {
  name                = "${var.project_name}"
  cluster             = "${aws_ecs_cluster.qtrees}"
  desired_count       = "1"
  task_definition     = "${aws_ecs_task_definition.postgrest_task.arn}"
  scheduling_strategy = "REPLICA"

  # 50 percent must be healthy during deploys
  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 100

  # TODO assign the vpc configs
  network_configuration {
    subnets = var.subnets
    security_groups = var.security_groups
  }

# TODO fix IP address
#   load_balancer {
#     target_group_arn = "${var.target_group_arn}"
#     container_name   = "${var.project_name}"
#     container_port   = "${var.container_port}"
#   }
}
