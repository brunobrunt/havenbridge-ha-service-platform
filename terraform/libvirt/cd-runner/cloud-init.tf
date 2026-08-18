# ---------------------------------------------------------
# Generate cloud-init configuration for the CD runner
# ---------------------------------------------------------

resource "libvirt_cloudinit_disk" "runner" {
  name = "${local.runner.hostname}-cloudinit"

  user_data = templatefile(
    "${path.module}/templates/user-data.yaml.tftpl",
    {
      hostname       = local.runner.hostname
      domain_name    = var.domain_name
      ssh_user       = var.ssh_user
      ssh_public_key = trimspace(file(pathexpand(var.ssh_public_key_path)))
      timezone       = var.timezone
    }
  )

  meta_data = yamlencode({
    "instance-id"    = local.runner.hostname
    "local-hostname" = local.runner.hostname
  })

  network_config = templatefile(
    "${path.module}/templates/network-config.yaml.tftpl",
    {
      mac_address    = local.runner.mac_address
      ip_address     = local.runner.ip_address
      network_prefix = var.network_prefix
      gateway        = var.gateway
      dns_servers    = var.dns_servers
      domain_name    = var.domain_name
    }
  )
}


# ---------------------------------------------------------
# Upload cloud-init disk to the libvirt storage pool
# ---------------------------------------------------------

resource "libvirt_volume" "cloudinit_iso" {
  name = "${local.runner.hostname}-cloudinit.iso"
  pool = libvirt_pool.cd_runner.name

  create = {
    content = {
      url = libvirt_cloudinit_disk.runner.path
    }
  }
}
