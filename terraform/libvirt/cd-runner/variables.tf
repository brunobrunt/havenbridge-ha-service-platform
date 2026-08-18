variable "libvirt_uri" {
  description = "Connection URI for the system-wide libvirt daemon on Syrus"
  type        = string
  default     = "qemu:///system"
}

variable "storage_pool_name" {
  description = "Name of the libvirt storage pool for the HavenBridge CD runner"
  type        = string
  default     = "havenbridge-cd-runner"
}

variable "storage_pool_path" {
  description = "Filesystem path where the HavenBridge CD runner disk will be stored"
  type        = string
}

variable "base_image_path" {
  description = "Path to the Ubuntu 24.04 QCOW2 cloud image"
  type        = string
}

variable "ssh_user" {
  description = "Administrative Linux user created on the CD runner VM"
  type        = string
  default     = "mino"
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key installed on the CD runner VM"
  type        = string
}

variable "network_name" {
  description = "Existing libvirt network used by the CD runner VM"
  type        = string
  default     = "default"
}

variable "network_prefix" {
  description = "CIDR prefix length for the CD runner network"
  type        = number
  default     = 24
}

variable "gateway" {
  description = "Default gateway used by the CD runner VM"
  type        = string
  default     = "172.16.10.1"
}

variable "dns_servers" {
  description = "DNS servers assigned to the CD runner VM"
  type        = list(string)

  default = [
    "1.1.1.1",
    "8.8.8.8"
  ]
}

variable "domain_name" {
  description = "Internal DNS domain used by the CD runner VM"
  type        = string
  default     = "everpresencehaven.internal"
}

variable "timezone" {
  description = "Timezone configured on the CD runner VM"
  type        = string
  default     = "America/Edmonton"
}
