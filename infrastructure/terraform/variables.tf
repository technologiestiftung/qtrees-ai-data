variable "region" {
  default     = "eu-central-1"
  description = "AWS region"
}

variable "project_name" {
  default     = "qtreestest"
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

# variable "POSTGRES_USER" {
#   description = "RDS root user"
#   sensitive   = true
# }

variable "POSTGRES_PASSWD" {
  description = "RDS root user password"
  sensitive   = true
}

variable "AWS_ACCOUNT_ID" {
  description = "account id"
  sensitive   = true
}