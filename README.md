# Network Automation CI/CD Pipeline
### GitHub Actions + Ansible + pyATS + Terraform

---

## Pipeline Flow

```
Git Push / PR
      ↓
┌─────────────────────────────────────────────────┐
│ JOB 1 — LINT                                    │
│   ansible-lint → Ansible syntax check           │
│   terraform fmt → terraform validate            │
└──────────────────────┬──────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│ JOB 2 — BACKUP  (on push to main)               │
│   Ansible saves all device configs              │
│   Uploaded as GitHub artifact (30 day retain)   │
└──────────────────────┬──────────────────────────┘
                       ↓
          ┌────────────┴────────────┐
          ↓                         ↓
┌─────────────────┐      ┌──────────────────────┐
│ JOB 3           │      │ JOB 4                │
│ PRE-CHANGE      │      │ TERRAFORM PLAN       │
│ pyATS snapshots │      │ Preview changes      │
│ device state    │      │ (safe — no apply)    │
└────────┬────────┘      └──────────┬───────────┘
         └────────────┬─────────────┘
                      ↓  (manual trigger only)
┌─────────────────────────────────────────────────┐
│ JOB 5 — ANSIBLE DEPLOY                          │
│   Push config to IOS-XE → NX-OS → FTD          │
└──────────────────────┬──────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│ JOB 6 — TERRAFORM APPLY                         │
│   Apply infrastructure changes                  │
└──────────────────────┬──────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│ JOB 7 — POST-CHANGE (pyATS)                     │
│   Validate device state vs pre-change snapshot  │
│   Fail pipeline if something regressed          │
└──────────────────────┬──────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│ JOB 8 — NOTIFY                                  │
│   MS Teams pass/fail notification               │
└─────────────────────────────────────────────────┘
```

---

## Stack & Role of Each Tool

| Tool | What It Does |
|---|---|
| **GitHub** | Stores code, triggers pipeline on push |
| **GitHub Actions** | Orchestrates all pipeline jobs |
| **Ansible** | Deploys config to IOS-XE, NX-OS, FTD |
| **pyATS** | Captures and compares device state |
| **Terraform** | Manages FMC policies and infra |

---

## Project Structure

```
network-automation-cicd/
│
├── .github/
│   └── workflows/
│       └── network-pipeline.yml      ← Main pipeline
│
├── ansible/
│   ├── site.yml                      ← Master playbook (all devices)
│   ├── backup.yml                    ← Backup device configs
│   ├── rollback.yml                  ← Emergency rollback
│   ├── requirements.yml              ← Ansible Galaxy collections
│   └── roles/
│       ├── iosxe/
│       │   ├── tasks/main.yml        ← IOS-XE config tasks
│       │   ├── handlers/main.yml     ← write memory on change
│       │   └── defaults/main.yml     ← default variables
│       ├── nxos/
│       │   ├── tasks/main.yml        ← NX-OS config tasks
│       │   ├── handlers/main.yml     ← copy run start on change
│       │   └── defaults/main.yml
│       └── ftd/
│           ├── tasks/main.yml        ← FTD via FMC REST API
│           ├── handlers/main.yml
│           └── defaults/main.yml
│
├── pyats/
│   ├── testbed.yaml                  ← Device connections for pyATS
│   └── tests/
│       ├── test_prechange.py         ← Snapshot state before change
│       └── test_postchange.py        ← Validate state after change
│
├── terraform/
│   ├── environments/
│   │   └── lab/
│   │       ├── main.tf               ← Calls all modules
│   │       └── variables.tf
│   └── modules/
│       ├── iosxe/                    ← IOS-XE Terraform resources
│       ├── nxos/                     ← NX-OS Terraform resources
│       └── ftd/                      ← FMC policy resources
│
├── ansible/
│   └── group_vars/
│       └── all.yml                   ← Shared vars (NTP, VLANs, SNMP)
│
├── inventory/
│   └── hosts.ini                     ← Ansible device inventory
│
├── ansible.cfg                       ← Ansible settings
├── requirements.txt                  ← Python packages
├── .env.example                      ← Copy to .env
└── .gitignore
```

---

## Quick Start

```bash
# 1. Clone repo
git clone https://github.com/YOUR_USERNAME/network-automation-cicd
cd network-automation-cicd

# 2. Install all dependencies
pip install -r requirements.txt
ansible-galaxy collection install -r ansible/requirements.yml

# 3. Set up credentials
cp .env.example .env
# Edit .env with your real device IPs and credentials

# 4. Test Ansible can reach devices (dry run)
ansible-playbook ansible/site.yml -i inventory/hosts.ini --check

# 5. Run pyATS pre-change snapshot locally
pytest pyats/tests/test_prechange.py -v

# 6. Terraform plan (safe preview)
terraform -chdir=terraform/environments/lab init
terraform -chdir=terraform/environments/lab plan
```

---

## GitHub Secrets Required

> Repo → Settings → Secrets and variables → Actions

| Secret | Used By |
|---|---|
| `NETWORK_USERNAME` | Ansible + pyATS |
| `NETWORK_PASSWORD` | Ansible + pyATS |
| `ENABLE_PASSWORD` | Ansible + pyATS (IOS-XE) |
| `IOSXE_R1_IP` | Ansible + pyATS |
| `IOSXE_R2_IP` | Ansible + pyATS |
| `IOSXE_SW1_IP` | Ansible + pyATS |
| `NXOS_SW1_IP` | Ansible + pyATS |
| `NXOS_SW2_IP` | Ansible + pyATS |
| `FTD_IP` | Ansible + pyATS |
| `FTD_USERNAME` | Ansible + pyATS |
| `FTD_PASSWORD` | Ansible + pyATS |
| `FMC_IP` | Ansible + Terraform |
| `FMC_USERNAME` | Ansible + Terraform |
| `FMC_PASSWORD` | Ansible + Terraform |
| `NTP_SERVER` | pyATS |
| `MGMT_GW` | pyATS |
| `SYSLOG_SERVER` | Terraform |
| `SNMP_COMMUNITY` | Ansible + Terraform |
| `TEAMS_WEBHOOK_URL` | Notifications |
| `AWS_ACCESS_KEY_ID` | Terraform backend |
| `AWS_SECRET_ACCESS_KEY` | Terraform backend |

---

## Triggering a Deployment

The pipeline runs **lint + backup + pre-change + terraform plan** automatically on every push.

To actually **deploy changes** to devices:

1. Go to **Actions** → **Network Automation Pipeline**
2. Click **Run workflow**
3. Set `run_deploy` → `true`
4. Set `environment` → `lab`
5. Click **Run workflow**

> Ansible Deploy and Terraform Apply only run when `run_deploy=true` on the `main` branch.

---

## Emergency Rollback

If a deployment breaks something:

```bash
ansible-playbook ansible/rollback.yml \
  -i inventory/hosts.ini \
  -e "backup_date=2026-03-09"
```

This restores all devices to the config backed up on that date.
