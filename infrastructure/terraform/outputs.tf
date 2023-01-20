# output "ec2_instance_id" {
#   value = aws_instance.qtrees.id
# }

output "db_private_address" {
  value = aws_db_instance.qtrees.address
}
