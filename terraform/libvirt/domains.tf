# This file declares the five KVM virtual machines used by the
# Ever Presence Haven Kubernetes cluster.
#
# Terraform creates one VM for every entry in local.nodes:
#
# - eph-cp01
# - eph-cp02
# - eph-cp03
# - eph-worker01
# - eph-worker02
#
# Each VM receives:
#
# - Its assigned vCPU and memory
# - Its own QCOW2 operating-system disk
# - Its own cloud-init ISO
# - A unique MAC address
# - A connection to the libvirt default network
# - A QEMU guest-agent communication channel


resource "libvirt_domain" "node" {
  # Create one virtual machine for every entry in local.nodes.
  for_each = local.nodes

  # VM name displayed by virsh and virt-manager.
  name = each.key

  # Use hardware-assisted KVM virtualization.
  type = "kvm"

  # Resource assignments come from locals.tf.
  memory      = each.value.memory_mib
  memory_unit = "MiB"
  vcpu        = each.value.vcpu

  # Expose the Dell host CPU features to the VM.
  #
  # The default qemu64 model does not provide the x86-64-v2
  # instruction level required by some modern container images.
  # Pass the physical host's CPU features through to the VM.

  cpu = {
    mode = "host-passthrough"
  }

  # Start the VM after Terraform creates it.
  running = true

  # Start the VM automatically when the physical host boots.
  autostart = true

  description = "Ever Presence Haven Kubernetes ${each.value.role} node"

  # Configure the virtual machine's boot environment.
  os = {
    type         = "hvm"
    type_arch    = "x86_64"
    type_machine = "q35"

    # Boot from the operating-system disk.
    boot_devices = [
      {
        dev = "hd"
      }
    ]
  }

  devices = {
    # -------------------------------------------------------
    # Storage devices
    # -------------------------------------------------------

    disks = [
      {
        # Main Ubuntu operating-system disk.
        device = "disk"

        source = {
          file = {
            file = libvirt_volume.node_disk[each.key].path
          }
        }

        driver = {
          name = "qemu"
          type = "qcow2"
        }

        # Present the disk inside Ubuntu as /dev/vda.
        target = {
          dev = "vda"
          bus = "virtio"
        }
      },

      {
        # Cloud-init configuration media.
        device = "cdrom"

        source = {
          file = {
            file = libvirt_volume.cloudinit_iso[each.key].path
          }
        }

        # Present the cloud-init ISO as read-only media.
        read_only = true

        target = {
          dev = "sda"
          bus = "sata"
        }
      }
    ]

    # -------------------------------------------------------
    # Network interface
    # -------------------------------------------------------

    interfaces = [
      {
        # Virtio provides an efficient virtual network adapter.
        model = {
          type = "virtio"
        }

        # The unique MAC address must match the address used in
        # network-config.yaml.tftpl.
        mac = {
          address = each.value.mac_address
        }

        # Connect the VM to the existing libvirt default network.
        source = {
          network = {
            network = var.network_name
          }
        }
      }
    ]

    # -------------------------------------------------------
    # QEMU guest-agent channel
    # -------------------------------------------------------

    channels = [
      {
        # Create a Unix socket between the host and guest.
        source = {
          unix = {
            mode = "bind"
          }
        }

        # qemu-guest-agent inside Ubuntu communicates through
        # this standard Virtio channel name.
        target = {
          virt_io = {
            name = "org.qemu.guest_agent.0"
          }
        }
      }
    ]
  }
}
