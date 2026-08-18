resource "libvirt_domain" "runner" {
  name = local.runner.hostname
  type = "kvm"

  memory      = local.runner.memory_mib
  memory_unit = "MiB"
  vcpu        = local.runner.vcpu

  cpu = {
    mode = "host-passthrough"
  }

  running   = true
  autostart = true

  description = "HavenBridge GitHub Actions CD runner"

  os = {
    type         = "hvm"
    type_arch    = "x86_64"
    type_machine = "q35"

    boot_devices = [
      {
        dev = "hd"
      }
    ]
  }

  devices = {
    disks = [
      {
        device = "disk"

        source = {
          file = {
            file = libvirt_volume.runner_disk.path
          }
        }

        driver = {
          name = "qemu"
          type = "qcow2"
        }

        target = {
          dev = "vda"
          bus = "virtio"
        }
      },

      {
        device = "cdrom"

        source = {
          file = {
            file = libvirt_volume.cloudinit_iso.path
          }
        }

        read_only = true

        target = {
          dev = "sda"
          bus = "sata"
        }
      }
    ]

    interfaces = [
      {
        model = {
          type = "virtio"
        }

        mac = {
          address = local.runner.mac_address
        }

        source = {
          network = {
            network = var.network_name
          }
        }
      }
    ]

    channels = [
      {
        source = {
          unix = {
            mode = "bind"
          }
        }

        target = {
          virt_io = {
            name = "org.qemu.guest_agent.0"
          }
        }
      }
    ]
  }
}
