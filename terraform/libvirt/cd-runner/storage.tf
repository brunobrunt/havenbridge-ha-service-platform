# ---------------------------------------------------------
# HavenBridge CD runner storage pool
# ---------------------------------------------------------

resource "libvirt_pool" "cd_runner" {
  name = var.storage_pool_name
  type = "dir"

  target = {
    path = var.storage_pool_path
  }
}


# ---------------------------------------------------------
# Ubuntu 24.04 base image
# ---------------------------------------------------------

resource "libvirt_volume" "ubuntu_base" {
  name = "ubuntu-24.04-base.qcow2"
  pool = libvirt_pool.cd_runner.name

  capacity = 4 * 1024 * 1024 * 1024

  target = {
    format = {
      type = "qcow2"
    }
  }

  create = {
    content = {
      url = var.base_image_path
    }
  }
}


# ---------------------------------------------------------
# HavenBridge CD runner disk
# ---------------------------------------------------------

resource "libvirt_volume" "runner_disk" {
  name = "${local.runner.hostname}.qcow2"
  pool = libvirt_pool.cd_runner.name

  capacity = local.runner.disk_size_gib * 1024 * 1024 * 1024

  backing_store = {
    path = libvirt_volume.ubuntu_base.path

    format = {
      type = "qcow2"
    }
  }

  target = {
    format = {
      type = "qcow2"
    }
  }
}
