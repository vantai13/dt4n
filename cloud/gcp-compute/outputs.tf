output "instance_names" {
  description = "GCE VM names."
  value       = google_compute_instance.dt4n[*].name
}

output "instance_self_links" {
  description = "GCE VM self links."
  value       = google_compute_instance.dt4n[*].self_link
}

output "public_ips" {
  description = "Public IPs. Neu reserve_static_ip=true thi day la reserved regional external IP."
  value = [
    for vm in google_compute_instance.dt4n :
    vm.network_interface[0].access_config[0].nat_ip
  ]
}

output "ssh_commands" {
  description = "Lenh SSH truc tiep vao tung GCE VM."
  value = [
    for ip in [
      for vm in google_compute_instance.dt4n :
      vm.network_interface[0].access_config[0].nat_ip
    ] :
    "ssh -i ${var.ssh_private_key_file} ${var.ssh_username}@${ip}"
  ]
}

output "gcloud_ssh_commands" {
  description = "Lenh SSH qua gcloud compute ssh."
  value = [
    for vm in google_compute_instance.dt4n :
    format(
      "gcloud compute ssh %s@%s --zone %s%s --ssh-key-file %s",
      var.ssh_username,
      vm.name,
      var.gcp_zone,
      var.gcp_project_id != "" ? " --project ${var.gcp_project_id}" : "",
      var.ssh_private_key_file
    )
  ]
}

output "bootstrap_log_commands" {
  description = "Theo doi qua trinh cai dat sau khi VM boot."
  value = [
    for ip in [
      for vm in google_compute_instance.dt4n :
      vm.network_interface[0].access_config[0].nat_ip
    ] :
    "ssh -i ${var.ssh_private_key_file} ${var.ssh_username}@${ip} 'tail -f /var/log/dt4n-bootstrap.log'"
  ]
}

output "sync_commands" {
  description = "Dong bo repo local hien tai len VM, gom code ditto/ va controller trong mininet/."
  value = [
    for ip in [
      for vm in google_compute_instance.dt4n :
      vm.network_interface[0].access_config[0].nat_ip
    ] :
    "./scripts/sync-project.sh ${var.ssh_username}@${ip} ${var.ssh_private_key_file} /home/${var.ssh_username}/${var.project_name}"
  ]
}

output "sync_ditto_commands" {
  description = "Dong bo checkout Eclipse Ditto local hien tai len VM va verify hash deployment/docker."
  value = [
    for ip in [
      for vm in google_compute_instance.dt4n :
      vm.network_interface[0].access_config[0].nat_ip
    ] :
    "./scripts/sync-ditto-deployment.sh ${var.ssh_username}@${ip} ${var.ssh_private_key_file} /home/${var.ssh_username}/tools/ditto"
  ]
}
