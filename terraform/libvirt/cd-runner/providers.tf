# The libvirt provider allows Terraform to manage KVM/libvirt
# infrastructure on the Syrus host.
#
# The URI is supplied through variables.tf rather than being
# hardcoded directly in this provider configuration.

provider "libvirt" {
  uri = var.libvirt_uri
}
