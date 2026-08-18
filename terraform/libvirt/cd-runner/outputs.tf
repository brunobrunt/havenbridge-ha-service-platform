output "runner_name" {
  description = "Name of the HavenBridge CD runner VM"
  value       = local.runner.hostname
}

output "runner_ip" {
  description = "IP address of the HavenBridge CD runner VM"
  value       = local.runner.ip_address
}

output "ssh_command" {
  description = "SSH command for connecting to the HavenBridge CD runner VM"
  value       = "ssh -i ~/.ssh/eph_k8s ${var.ssh_user}@${local.runner.ip_address}"
}

output "storage_pool" {
  description = "Libvirt storage pool used by the HavenBridge CD runner"

  value = {
    name = libvirt_pool.cd_runner.name
    path = var.storage_pool_path
  }
}
