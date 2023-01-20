# locals {
#   # this is the namespace for the ssm param system
#   # used by the app to fetch params at startup, see scripts/param.py
#   app_name = "${var.vpc_name}-${var.app_name}"
# }

resource "aws_ecs_service" "service" {
  name                = "${var.project_name}"
#   cluster             = "${var.cluster}"
  desired_count       = "1"
  task_definition     = "${aws_ecs_task_definition.app.arn}"
  scheduling_strategy = "REPLICA"

  # 50 percent must be healthy during deploys
  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 100

# TODO fix IP address
#   load_balancer {
#     target_group_arn = "${var.target_group_arn}"
#     container_name   = "${var.project_name}"
#     container_port   = "${var.container_port}"
#   }
}

# scheduled tasks
# https://docs.aws.amazon.com/AmazonECS/latest/developerguide/scheduled_tasks.html  
# https://vthub.medium.com/running-ecs-fargate-tasks-on-a-schedule-fd1ca428e669

# ecs task file
# https://github.com/navapbc/tf-ecs-example/tree/master/templates/basic-app/ecs-tasks
data "template_file" "task_definition" {
  template = "${file("${path.module}/task_definitions/postgrest_task.json")}"

  vars {
    docker_image_url = "${var.postgrest_docker_image}"
    container_name   = "${var.project_name}"
    aws_region       = "${var.region}"
    ssm_path         = "/${var.vpc_name}/${var.app_name}"
    container_port   = "${var.container_port}"
    health_check     = "${var.health_check}"
  }
}

resource "aws_ecs_task_definition" "app" {
  family                = "${var.project_name}"
  container_definitions = "${data.template_file.task_definition.rendered}"
}