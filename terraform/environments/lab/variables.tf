# =============================================================
# terraform/environments/lab/variables.tf
# =============================================================

variable "network_username" {
  description = "SSH username for IOS-XE and NX-OS devices"
  type        = string
  sensitive   = true
}

variable "network_password" {
  description = "SSH password for IOS-XE and NX-OS devices"
  type        = string
  sensitive   = true
}

variable "fmc_username" {
  description = "FMC admin username"
  type        = string
  sensitive   = true
}

variable "fmc_password" {
  description = "FMC admin password"
  type        = string
  sensitive   = true
}

variable "iosxe_r1_ip" {
  description = "IOS-XE Router 01 IP address"
  type        = string
}

variable "nxos_sw1_ip" {
  description = "NX-OS Switch 01 IP address"
  type        = string
}

variable "fmc_ip" {
  description = "FMC IP address"
  type        = string
}

variable "syslog_server" {
  description = "Syslog server IP"
  type        = string
  default     = "10.0.10.100"
}

variable "snmp_community" {
  description = "SNMP read-only community string"
  type        = string
  sensitive   = true
  default     = "public"
}
