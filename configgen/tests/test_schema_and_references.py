import copy

import pytest
import yaml
from conftest import TOPOLOGY_DIR

from avionics_configgen.loader import TopologyLoadError, load_topology
from avionics_configgen.planner import plan_topology
from avionics_configgen.validator import TopologyValidationError


@pytest.fixture
def real_topology():
    with open(TOPOLOGY_DIR / "avionics-real.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def demo_topology():
    with open(TOPOLOGY_DIR / "demo-vlsm-example.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_real_topology_loads_and_plans_cleanly():
    topology = load_topology(TOPOLOGY_DIR / "avionics-real.yaml")
    result = plan_topology(topology)
    assert len(result.devices) == 11
    assert len(result.vlan_subnets) == 20


def test_demo_topology_loads_and_plans_cleanly():
    topology = load_topology(TOPOLOGY_DIR / "demo-vlsm-example.yaml")
    result = plan_topology(topology)
    assert len(result.devices) == 3
    assert len(result.vlan_subnets) == 3


def test_schema_rejects_unknown_top_level_field(real_topology):
    import jsonschema

    from avionics_configgen.loader import load_schema

    broken = copy.deepcopy(real_topology)
    broken["not_a_real_field"] = True
    schema = load_schema()
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(broken, schema)


def test_validator_rejects_link_to_unknown_device(real_topology):
    broken = copy.deepcopy(real_topology)
    broken["links"]["fw-hq"]["endpoints"][0]["device"] = "NoSuchDevice"
    with pytest.raises(TopologyValidationError):
        plan_topology(broken)


def test_validator_rejects_interface_claimed_by_two_links(real_topology):
    broken = copy.deepcopy(real_topology)
    # Point a second link at an interface already claimed by "fw-hq".
    broken["links"]["hq-amf"]["endpoints"][0] = {"device": "HQ-Router", "interface": "GigabitEthernet0/1"}
    with pytest.raises(TopologyValidationError):
        plan_topology(broken)


def test_validator_rejects_vlan_gateway_interface_collision(demo_topology):
    broken = copy.deepcopy(demo_topology)
    broken["devices"]["DEMO-HQ-SW1"]["interfaces"]["Vlan10"] = {"mode": "routed"}
    with pytest.raises(TopologyValidationError):
        plan_topology(broken)


def test_validator_rejects_duplicate_vlan_id_within_site(real_topology):
    broken = copy.deepcopy(real_topology)
    broken["vlans"][1]["id"] = broken["vlans"][0]["id"]  # duplicate within hq
    broken["vlans"][1]["site"] = broken["vlans"][0]["site"]
    with pytest.raises(TopologyValidationError):
        plan_topology(broken)


def test_validator_rejects_unknown_allowed_vlan(real_topology):
    broken = copy.deepcopy(real_topology)
    broken["devices"]["HQ-DistSwitch"]["interfaces"]["GigabitEthernet0/1"]["allowed_vlans"] = [9999]
    with pytest.raises(TopologyValidationError):
        plan_topology(broken)


def test_load_topology_raises_on_malformed_yaml(tmp_path):
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("version: 1\nsites: not-an-object\n", encoding="utf-8")
    with pytest.raises(TopologyLoadError):
        load_topology(bad_file)
