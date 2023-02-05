variable "region" {
  default     = "eu-central-1"
  description = "AWS region"
}

variable "project_name" {
  default     = "qtreesdev"
  description = "Project name used to init and tag provisioned resources"
}

variable "qtrees_version" {
  default     = "v2"
}

variable "restricted" {
  default = true
}

variable "pub_key" {
  description = "public key used in provisioned EC2 instance"
  sensitive   = true
}

variable "private_key" {
  description = "private key used for ssh connection"
  sensitive   = true
}

variable "ELASTIC_IP_EC2" {
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
variable "DB_ADMIN_PASSWD" {
  sensitive   = true
}
variable "DB_USER_PASSWD" {
  sensitive   = true
}
variable "UI_USER_PASSWD" {
  sensitive   = true
}

variable "POSTGRES_PASSWD" {
  description = "RDS root user password"
  sensitive   = true
}
