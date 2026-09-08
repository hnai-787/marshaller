import yaml
from conftest import GOLDEN_DIR, TOPOLOGY_DIR

from avionics_configgen.planner import plan_topology
from avionics_configgen.renderer import render_device


def _load(name):
    with open(TOPOLOGY_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _assert_matches_golden(device_name, model, golden_path):
    actual = render_device(model)
    expected = golden_path.read_text(encoding="utf-8")
    assert actual == expected, f"{device_name} config no longer matches its golden file"


def test_real_topology_devices_match_golden_files():
    result = plan_topology(_load("avionics-real.yaml"))
    for device_name in ("HQ-Router", "HQ-DistSwitch", "HQ-FW", "AMF-Router"):
        _assert_matches_golden(device_name, result.devices[device_name], GOLDEN_DIR / "real" / f"{device_name}.cfg")


def test_demo_topology_devices_match_golden_files():
    result = plan_topology(_load("demo-vlsm-example.yaml"))
    for device_name in ("DEMO-HQ-R1", "DEMO-HQ-SW1", "DEMO-BR-R1"):
        _assert_matches_golden(device_name, result.devices[device_name], GOLDEN_DIR / "demo" / f"{device_name}.cfg")


def test_generated_config_has_no_double_ip_address_lines():
    """Regression test for the real duplicate-interface bug found while
    building the demo topology: an "ip address" line must appear at most
    once per interface stanza.
    """
    result = plan_topology(_load("avionics-real.yaml"))
    for name, model in result.devices.items():
        text = render_device(model)
        interface_names = [i.name for i in model.interfaces]
        assert len(interface_names) == len(set(interface_names)), f"{name} has duplicate interface names"
        assert "!!\n" not in text
