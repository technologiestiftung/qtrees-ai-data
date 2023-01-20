variable "region" {
  default     = "eu-central-1"
  description = "AWS region"
}

variable "project_name" {
  default     = "qtreesdev"
  description = "Project name used to init and tag provisioned resources"
}

variable "qtrees_version" {
  default     = "v3"
}

variable "pub_key" {
  description = "public key used in provisioned EC2 instance"
  sensitive   = true
}

variable "private_key" {
  description = "private key used for ssh connection"
  sensitive   = true
}

variable "GIS_PASSWD" {
  sensitive   = true
}
variable "AUTH_PASSWD" {
  sensitive   = true
}
variable "JWT_SECRET" {
  sensitive   = true
}

variable "POSTGRES_PASSWD" {
  description = "RDS root user password"
  sensitive   = true
}

variable "postgrest_docker_image" {
  default = "257772343150.dkr.ecr.eu-central-1.amazonaws.com/test_repo:latest"
}



variable "target_group_arn" {
  description = "load balancing target for your service"
}

variable "container_port" {
  description = "Port that this container listens on. If you change this from default, you must supply a new healthcheck"
  default = "3000"
}

variable "health_check" {
  description = "Health check to determine if a spawned task is operational."
  default = "wget --quiet http://localhost:3000 || exit 1"
}
