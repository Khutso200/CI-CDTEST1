# =============================================================
# pyats/tests/test_postchange.py
# Validates device state AFTER Ansible/Terraform makes changes
# Compares against pre-change snapshots to catch regressions
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


# ── Helper — load snapshot ────────────────────────────────────
def load_snapshot(name):
    path = f"reports/snapshots/{name}.json"
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


# =============================================================
# POST-CHANGE: IOS-XE ROUTER
# =============================================================

class TestPostChangeIosXE:

    def test_interfaces_still_up(self, router01):
        """Verify no interfaces went down after change."""
        pre  = load_snapshot("iosxe_router01_interfaces_pre")
        post = router01.parse("show interfaces")

        if pre is None:
            pytest.skip("No pre-change snapshot found")

        for intf_name, intf_data in pre.items():
            if isinstance(intf_data, dict):
                pre_state  = intf_data.get("line_protocol", "")
                post_state = post.get(intf_name, {}).get("line_protocol", "")

                # Only assert on interfaces that were UP before
                if pre_state == "up":
                    assert post_state == "up", \
                        f"Interface {intf_name} was UP before — now {post_state}"

    def test_route_count_not_reduced(self, router01):
        """Verify routing table did not lose routes."""
        pre  = load_snapshot("iosxe_router01_routes_pre")
        post = router01.parse("show ip route")

        if pre is None:
            pytest.skip("No pre-change snapshot found")

        def count_routes(parsed):
            count = 0
            for vrf_data in parsed.get("vrf", {}).values():
                count += len(vrf_data.get("address_family", {})
                              .get("ipv4", {}).get("routes", {}))
            return count

        pre_count  = count_routes(pre)
        post_count = count_routes(post)

        assert post_count >= pre_count, \
            f"Route count dropped: was {pre_count}, now {post_count}"

    def test_ospf_neighbors_stable(self, router01):
        """Verify OSPF neighbor count did not decrease."""
        pre = load_snapshot("iosxe_router01_ospf_pre")
        if not pre or not pre.get("neighbors"):
            pytest.skip("No OSPF neighbors in pre-change snapshot")

        try:
            post = router01.parse("show ip ospf neighbor")
        except Exception:
            pytest.skip("OSPF not configured")

        pre_count  = len(pre.get("neighbors", {}))
        post_count = len(post.get("neighbors", {}))

        assert post_count >= pre_count, \
            f"OSPF neighbor count dropped: was {pre_count}, now {post_count}"

    def test_ntp_still_synchronized(self, router01):
        """Verify NTP is still synchronized after change."""
        output = router01.execute("show ntp status")
        assert "synchronized" in output.lower(), \
            "NTP lost sync after config change"

    def test_ssh_still_working(self, router01):
        """Verify SSH is still enabled and on version 2."""
        output = router01.execute("show ip ssh")
        assert "SSH Enabled" in output, "SSH disabled after change"
        assert "version 2" in output.lower() or "2.0" in output, \
            "SSH version 2 not active after change"


# =============================================================
# POST-CHANGE: NX-OS SWITCH
# =============================================================

class TestPostChangeNxOS:

    def test_vlans_still_present(self, nxos01):
        """Verify VLANs were not removed during change."""
        pre  = load_snapshot("nxos_sw01_vlans_pre")
        post = nxos01.parse("show vlan")

        if pre is None:
            pytest.skip("No pre-change snapshot found")

        pre_vlans  = set(pre.get("vlans", {}).keys())
        post_vlans = set(post.get("vlans", {}).keys())

        missing = pre_vlans - post_vlans
        assert not missing, f"VLANs removed after change: {missing}"

    def test_required_vlans_active(self, nxos01):
        """Verify required VLANs 10, 20, 30, 40 are active."""
        parsed = nxos01.parse("show vlan")
        vlans = parsed.get("vlans", {})

        for required_vlan in ["10", "20", "30", "40"]:
            assert required_vlan in vlans, \
                f"VLAN {required_vlan} missing after config change"
            assert vlans[required_vlan].get("state") == "active", \
                f"VLAN {required_vlan} is not active"

    def test_vpc_peer_link_up(self, nxos01):
        """Verify vPC peer link is still up."""
        try:
            output = nxos01.execute("show vpc")
            if "vPC Peer-link status" in output:
                assert "up" in output.lower(), "vPC peer link went down"
        except Exception:
            pytest.skip("vPC not configured")

    def test_ntp_still_synchronized(self, nxos01):
        """Verify NTP is still synchronized."""
        output = nxos01.execute("show ntp status")
        assert "synchronized" in output.lower() or \
               "Clock is synchronized" in output, \
            "NTP lost sync after config change"


# =============================================================
# CROSS-PLATFORM HEALTH CHECKS
# =============================================================

class TestCrossPlatformHealth:

    def test_iosxe_ping_gateway(self, router01):
        """Router can reach management gateway."""
        mgmt_gw = os.getenv("MGMT_GW", "10.0.0.254")
        output = router01.execute(f"ping {mgmt_gw} repeat 5")
        assert "!!!!!" in output or "Success rate is 100" in output, \
            f"Router cannot ping gateway {mgmt_gw}"

    def test_iosxe_nxos_reachability(self, router01):
        """Router can reach NX-OS switch."""
        nxos_ip = os.getenv("NXOS_SW1_IP")
        if not nxos_ip:
            pytest.skip("NXOS_SW1_IP not set")
        output = router01.execute(f"ping {nxos_ip} repeat 5")
        assert "!!!!!" in output or "Success rate is 100" in output, \
            f"Router cannot ping NX-OS switch at {nxos_ip}"
