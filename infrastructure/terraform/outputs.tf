output "ec2_instance_id" {
  value = aws_instance.qtrees.id
}

output "eip_public_dns" {
  value = aws_eip.qtrees.public_dns
}

output "db_private_address" {
  value = aws_db_instance.qtrees.address
}

output "dns_name" {
  value = aws_lb.qtrees.dns_name
}
