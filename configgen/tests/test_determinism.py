import copy

import yaml
from conftest import TOPOLOGY_DIR

from avionics_configgen.planner import plan_topology
from avionics_configgen.renderer import render_device


def _load(name):
    with open(TOPOLOGY_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_regenerating_the_same_topology_is_byte_identical():
    topology = _load("avionics-real.yaml")
    result1 = plan_topology(copy.deepcopy(topology))
    result2 = plan_topology(copy.deepcopy(topology))

    for name in result1.devices:
        assert render_device(result1.devices[name]) == render_device(result2.devices[name])


def test_reordering_devices_dict_does_not_change_output():
    topology = _load("avionics-real.yaml")
    reordered = copy.deepcopy(topology)
    reordered["devices"] = dict(reversed(list(reordered["devices"].items())))
    reordered["links"] = dict(reversed(list(reordered["links"].items())))
    reordered["vlans"] = list(reversed(reordered["vlans"]))

    result_original = plan_topology(copy.deepcopy(topology))
    result_reordered = plan_topology(reordered)

    for name in result_original.devices:
        original_text = render_device(result_original.devices[name])
        reordered_text = render_device(result_reordered.devices[name])
        assert original_text == reordered_text, f"{name} config changed when input ordering changed"

    assert result_original.vlan_subnets == result_reordered.vlan_subnets
    assert result_original.link_subnets == result_reordered.link_subnets


def test_reversing_link_endpoint_order_does_not_change_addresses():
    topology = _load("demo-vlsm-example.yaml")
    reversed_topology = copy.deepcopy(topology)
    reversed_topology["links"]["hq-branch"]["endpoints"] = list(
        reversed(reversed_topology["links"]["hq-branch"]["endpoints"])
    )

    result_original = plan_topology(copy.deepcopy(topology))
    result_reversed = plan_topology(reversed_topology)

    assert result_original.link_endpoint_addresses == result_reversed.link_endpoint_addresses
