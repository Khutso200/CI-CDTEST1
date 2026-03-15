# =============================================================
# pyats/tests/test_prechange.py
# Captures device state BEFORE Ansible/Terraform makes changes
# Saves snapshots to compare against post-change state
# =============================================================

import os
import json
import pytest
from pyats.topology import loader


# ── Load testbed ─────────────────────────────────────────────
@pytest.fixture(scope="session")
def testbed():
    tb = loader.load("pyats/testbed.yaml")
    return tb


@pytest.fixture(scope="session")
def router01(testbed):
    device = testbed.devices["iosxe-router-01"]
    device.connect(log_stdout=False)
    yield device
    device.disconnect()


@pytest.fixture(scope="session")
def nxos01(testbed):
    device = testbed.devices["nxos-switch-01"]
    device.connect(log_stdout=False)
    yield device
    device.disconnect()


# ── Helper — save snapshot ────────────────────────────────────
def save_snapshot(name, data):
    os.makedirs("reports/snapshots", exist_ok=True)
    path = f"reports/snapshots/{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  Snapshot saved: {path}")


# =============================================================
# PRE-CHANGE: IOS-XE ROUTER
# =============================================================

class TestPreChangeIosXE:

    def test_capture_interfaces(self, router01):
        """Capture interface state before change."""
        parsed = router01.parse("show interfaces")
        save_snapshot("iosxe_router01_interfaces_pre", parsed)
        assert parsed is not None, "Failed to parse interfaces"

    def test_capture_routing_table(self, router01):
        """Capture routing table before change."""
        parsed = router01.parse("show ip route")
        save_snapshot("iosxe_router01_routes_pre", parsed)
        assert "vrf" in parsed, "Routing table parse failed"

    def test_capture_ospf_neighbors(self, router01):
        """Capture OSPF neighbor state before change."""
        try:
            parsed = router01.parse("show ip ospf neighbor")
            save_snapshot("iosxe_router01_ospf_pre", parsed)
        except Exception:
            save_snapshot("iosxe_router01_ospf_pre", {"neighbors": {}})

    def test_capture_bgp_summary(self, router01):
        """Capture BGP summary before change."""
        try:
            parsed = router01.parse("show bgp all summary")
            save_snapshot("iosxe_router01_bgp_pre", parsed)
        except Exception:
            save_snapshot("iosxe_router01_bgp_pre", {})

    def test_capture_version(self, router01):
        """Capture device version info."""
        parsed = router01.parse("show version")
        save_snapshot("iosxe_router01_version", parsed)
        assert parsed is not None


# =============================================================
# PRE-CHANGE: NX-OS SWITCH
# =============================================================

class TestPreChangeNxOS:

    def test_capture_vlans(self, nxos01):
        """Capture VLAN table before change."""
        parsed = nxos01.parse("show vlan")
        save_snapshot("nxos_sw01_vlans_pre", parsed)
        assert parsed is not None, "Failed to parse VLAN table"

    def test_capture_interfaces(self, nxos01):
        """Capture interface state before change."""
        parsed = nxos01.parse("show interface status")
        save_snapshot("nxos_sw01_interfaces_pre", parsed)
        assert parsed is not None

    def test_capture_vpc(self, nxos01):
        """Capture vPC state before change."""
        try:
            parsed = nxos01.parse("show vpc")
            save_snapshot("nxos_sw01_vpc_pre", parsed)
        except Exception:
            save_snapshot("nxos_sw01_vpc_pre", {})

    def test_capture_bgp(self, nxos01):
        """Capture BGP summary before change."""
        try:
            parsed = nxos01.parse("show bgp all summary")
            save_snapshot("nxos_sw01_bgp_pre", parsed)
        except Exception:
            save_snapshot("nxos_sw01_bgp_pre", {})
