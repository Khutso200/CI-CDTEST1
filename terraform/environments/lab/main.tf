# =============================================================
# terraform/environments/lab/main.tf
# Lab environment — calls all 3 device modules
# =============================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    iosxe = {
      source  = "CiscoDevNet/iosxe"
      version = "~> 0.5"
    }
    nxos = {
      source  = "CiscoDevNet/nxos"
      version = "~> 0.5"
    }
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "~> 1.2"
    }
  }

  # Remote state — store in S3 so GitHub Actions can access it
  backend "s3" {
    bucket = "tectura-terraform-state"
    key    = "network/lab/terraform.tfstate"
    region = "af-south-1"
  }
}

# ── IOS-XE Provider ──────────────────────────────────────────
provider "iosxe" {
  username = var.network_username
  password = var.network_password
  url      = "https://${var.iosxe_r1_ip}"
  insecure = true
}

# ── NX-OS Provider ───────────────────────────────────────────
provider "nxos" {
  username = var.network_username
  password = var.network_password
  url      = "https://${var.nxos_sw1_ip}"
  insecure = true
}

# ── FMC Provider ─────────────────────────────────────────────
provider "fmc" {
  fmc_username = var.fmc_username
  fmc_password = var.fmc_password
  fmc_host     = var.fmc_ip
  fmc_insecure = true
}

# ── Modules ───────────────────────────────────────────────────
module "iosxe" {
  source = "../../modules/iosxe"

  vlans = {
    "10" = { name = "MGMT" }
    "20" = { name = "DATA" }
    "30" = { name = "VOICE" }
    "40" = { name = "DMZ" }
  }

  ntp_servers    = ["196.4.160.4", "196.4.160.5"]
  syslog_server  = var.syslog_server
  snmp_community = var.snmp_community
}

module "nxos" {
  source = "../../modules/nxos"

  vlans = {
    "10" = { name = "MGMT" }
    "20" = { name = "DATA" }
    "30" = { name = "VOICE" }
    "40" = { name = "DMZ" }
  }

  vpc_domain_id  = 10
  ntp_servers    = ["196.4.160.4"]
  syslog_server  = var.syslog_server
  snmp_community = var.snmp_community
}

module "ftd" {
  source      = "../../modules/ftd"
  policy_name = "LAB-SECURITY-POLICY"
}
