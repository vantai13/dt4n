output "instance_ids" {
  description = "EC2 instance IDs."
  value       = aws_instance.dt4n[*].id
}

output "public_ips" {
  description = "Public IPs. Neu allocate_elastic_ip=true thi day la EIP co dinh."
  value       = var.allocate_elastic_ip ? aws_eip.dt4n[*].public_ip : aws_instance.dt4n[*].public_ip
}

output "ssh_commands" {
  description = "Lenh SSH vao tung EC2."
  value = [
    for ip in(var.allocate_elastic_ip ? aws_eip.dt4n[*].public_ip : aws_instance.dt4n[*].public_ip) :
    "ssh -i ${var.ssh_private_key_file} ubuntu@${ip}"
  ]
}

output "ssm_commands" {
  description = "Lenh vao EC2 bang Session Manager neu AWS CLI/SSM da cau hinh."
  value = [
    for id in aws_instance.dt4n[*].id :
    "aws ssm start-session --target ${id} --region ${var.aws_region}"
  ]
}

output "bootstrap_log_commands" {
  description = "Theo doi qua trinh cai dat sau khi EC2 boot."
  value = [
    for ip in(var.allocate_elastic_ip ? aws_eip.dt4n[*].public_ip : aws_instance.dt4n[*].public_ip) :
    "ssh -i ${var.ssh_private_key_file} ubuntu@${ip} 'tail -f /var/log/dt4n-bootstrap.log'"
  ]
}

output "sync_commands" {
  description = "Dong bo repo local hien tai len EC2, gom code ditto/ va controller Ryu trong mininet/."
  value = [
    for ip in(var.allocate_elastic_ip ? aws_eip.dt4n[*].public_ip : aws_instance.dt4n[*].public_ip) :
    "./scripts/sync-project.sh ubuntu@${ip} ${var.ssh_private_key_file} /home/ubuntu/${var.project_name}"
  ]
}
