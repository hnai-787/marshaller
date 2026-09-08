"""Topology invariant checks beyond JSON-schema shape validation.

These check the things a schema can't: that references actually resolve,
that no interface is claimed by two links, and (after planning) that the
resolved addressing obeys the invariants the research brief calls for --
no overlapping subnets, every address inside its own subnet, etc.
"""

from __future__ import annotations

from ipaddress import IPv4Network
from typing import Any


class TopologyValidationError(Exception):
    pass


def validate_references(topology: dict[str, Any]) -> None:
    errors: list[str] = []

    sites = topology["sites"]
    devices = topology["devices"]
    links = topology["links"]
    pools = topology["address_pools"]
    profiles = topology.get("profiles", {})

    for dev_name, dev in devices.items():
        if dev["site"] not in sites:
            errors.append(f"device {dev_name}: unknown site '{dev['site']}'")
        profile = dev.get("hardening_profile")
        if profile is not None and profile not in profiles:
            errors.append(f"device {dev_name}: unknown hardening_profile '{profile}'")
        for if_name, iface in dev["interfaces"].items():
            link_name = iface.get("link")
            if link_name is not None and link_name not in links:
                errors.append(f"device {dev_name} interface {if_name}: unknown link '{link_name}'")

    # every link must reference exactly two distinct, existing (device, interface) endpoints,
    # and no (device, interface) pair may be claimed by more than one link.
    claimed: dict[tuple[str, str], str] = {}
    for link_name, link in links.items():
        pool_name = link["allocation"].get("pool")
        if link["allocation"]["mode"] == "computed" and pool_name not in pools:
            errors.append(f"link {link_name}: unknown pool '{pool_name}'")

        endpoints = link["endpoints"]
        seen_pairs = set()
        for ep in endpoints:
            pair = (ep["device"], ep["interface"])
            if pair in seen_pairs:
                errors.append(f"link {link_name}: duplicate endpoint {pair}")
            seen_pairs.add(pair)

            if ep["device"] not in devices:
                errors.append(f"link {link_name}: unknown device '{ep['device']}'")
                continue
            if ep["interface"] not in devices[ep["device"]]["interfaces"]:
                errors.append(f"link {link_name}: device '{ep['device']}' has no interface '{ep['interface']}'")
                continue

            if pair in claimed and claimed[pair] != link_name:
                errors.append(f"interface {pair} claimed by both link '{claimed[pair]}' and '{link_name}'")
            claimed[pair] = link_name

    seen_vlan_ids_per_site: dict[str, set[int]] = {}
    for vlan in topology["vlans"]:
        if vlan["site"] not in sites:
            errors.append(f"vlan {vlan['id']}: unknown site '{vlan['site']}'")
        pool_name = vlan["allocation"].get("pool")
        if vlan["allocation"]["mode"] == "computed" and pool_name not in pools:
            errors.append(f"vlan {vlan['id']}: unknown pool '{pool_name}'")
        gateway = vlan.get("gateway")
        if gateway is not None:
            if gateway["device"] not in devices:
                errors.append(f"vlan {vlan['id']}: unknown gateway device '{gateway['device']}'")
            elif gateway["interface"] in devices[gateway["device"]]["interfaces"]:
                # The gateway interface is synthesized by the planner from
                # this field alone -- also declaring it under the device's
                # own `interfaces` map produces two stanzas with the same
                # name in the rendered config (found via a real duplicate
                # "interface Vlan10" bug while building the demo topology).
                errors.append(
                    f"vlan {vlan['id']}: gateway interface '{gateway['interface']}' on "
                    f"'{gateway['device']}' is also manually declared under that device's "
                    f"interfaces -- remove the manual declaration, it is synthesized automatically"
                )

        seen_vlan_ids_per_site.setdefault(vlan["site"], set())
        if vlan["id"] in seen_vlan_ids_per_site[vlan["site"]]:
            errors.append(f"vlan {vlan['id']}: duplicate VLAN id within site '{vlan['site']}'")
        seen_vlan_ids_per_site[vlan["site"]].add(vlan["id"])

    all_vlan_ids = {vlan["id"] for vlan in topology["vlans"]}
    for dev_name, dev in devices.items():
        for if_name, iface in dev["interfaces"].items():
            for vid in iface.get("allowed_vlans", []) or []:
                if vid not in all_vlan_ids:
                    errors.append(f"device {dev_name} interface {if_name}: allowed_vlans references unknown VLAN {vid}")
            access_vlan = iface.get("access_vlan")
            if access_vlan is not None and access_vlan not in all_vlan_ids:
                errors.append(f"device {dev_name} interface {if_name}: access_vlan references unknown VLAN {access_vlan}")

    if errors:
        raise TopologyValidationError("Topology reference validation failed:\n  " + "\n  ".join(errors))


def validate_resolved_addressing(
    subnets: list[IPv4Network],
    address_assignments: list[tuple[str, str]],
) -> None:
    """Post-allocation invariant checks (research brief, section 10).

    `subnets` is every allocated/fixed subnet in the topology.
    `address_assignments` is (address, containing_subnet_str) pairs to
    confirm each assigned address actually falls inside the subnet it
    was assigned from.
    """
    errors: list[str] = []

    for i, a in enumerate(subnets):
        for b in subnets[i + 1 :]:
            if a.overlaps(b):
                errors.append(f"allocated subnets overlap: {a} and {b}")

    subnet_by_str = {str(net): net for net in subnets}
    for address, subnet_str in address_assignments:
        net = subnet_by_str.get(subnet_str)
        if net is None:
            errors.append(f"address {address}: references unknown subnet {subnet_str}")
            continue
        from ipaddress import IPv4Address

        if IPv4Address(address) not in net:
            errors.append(f"address {address} is not inside its assigned subnet {subnet_str}")

    if errors:
        raise TopologyValidationError("Resolved addressing validation failed:\n  " + "\n  ".join(errors))
