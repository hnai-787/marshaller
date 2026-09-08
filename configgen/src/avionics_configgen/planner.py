"""Resolve a validated topology into per-device DeviceConfigModel objects.

This is the "device-independent calculations happen in code, not in
templates" boundary the research brief insists on: every IP address in
the resulting models is already a concrete string by the time a template
sees it.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv4Network

from .ipam import (
    AllocationRequest,
    allocate_blocks,
    first_usable,
    hosts_to_prefix,
    nth_usable,
)
from .models import (
    DeviceConfigModel,
    HardeningConfig,
    OspfConfig,
    OspfNetwork,
    ResolvedInterface,
    VlanDefinition,
)
from .validator import validate_references, validate_resolved_addressing


@dataclass(frozen=True)
class PlanResult:
    vlan_subnets: dict[int, IPv4Network]
    vlan_gateways: dict[int, str]
    link_subnets: dict[str, IPv4Network]
    link_endpoint_addresses: dict[tuple[str, str], str]
    devices: dict[str, DeviceConfigModel]


def _resolve_pools(topology: dict) -> dict[str, IPv4Network]:
    return {name: IPv4Network(cfg["cidr"]) for name, cfg in topology["address_pools"].items()}


def _resolve_vlan_subnets(topology: dict, pools: dict[str, IPv4Network]) -> dict[int, IPv4Network]:
    fixed: dict[int, IPv4Network] = {}
    requests_by_pool: dict[str, list[AllocationRequest]] = {}
    key_to_vlan_id: dict[tuple, int] = {}

    for vlan in topology["vlans"]:
        alloc = vlan["allocation"]
        if alloc["mode"] == "fixed":
            fixed[vlan["id"]] = IPv4Network(alloc["subnet"])
        else:
            key = (vlan["site"], vlan["id"])
            prefix = hosts_to_prefix(alloc["hosts_required"])
            requests_by_pool.setdefault(alloc["pool"], []).append(AllocationRequest(key=key, prefix=prefix))
            key_to_vlan_id[key] = vlan["id"]

    resolved = dict(fixed)
    for pool_name, requests in requests_by_pool.items():
        allocated = allocate_blocks(pools[pool_name], requests)
        for key, net in allocated.items():
            resolved[key_to_vlan_id[key]] = net

    return resolved


def _resolve_link_subnets(topology: dict, pools: dict[str, IPv4Network]) -> dict[str, IPv4Network]:
    fixed: dict[str, IPv4Network] = {}
    requests_by_pool: dict[str, list[AllocationRequest]] = {}

    for link_name, link in topology["links"].items():
        alloc = link["allocation"]
        if alloc["mode"] == "fixed":
            fixed[link_name] = IPv4Network(alloc["subnet"])
        else:
            key = (link_name,)
            requests_by_pool.setdefault(alloc["pool"], []).append(
                AllocationRequest(key=key, prefix=alloc["prefix_length"])
            )

    resolved = dict(fixed)
    for pool_name, requests in requests_by_pool.items():
        allocated = allocate_blocks(pools[pool_name], requests)
        for key, net in allocated.items():
            resolved[key[0]] = net

    return resolved


def _resolve_link_endpoint_addresses(
    topology: dict, link_subnets: dict[str, IPv4Network]
) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}

    for link_name, link in topology["links"].items():
        subnet = link_subnets[link_name]
        endpoints = link["endpoints"]

        explicit = [ep for ep in endpoints if "address" in ep]
        if explicit:
            for ep in endpoints:
                result[(ep["device"], ep["interface"])] = ep["address"]
            continue

        # No explicit addresses given (computed/demo links): assign
        # deterministically by canonical (device, interface) sort order,
        # so reversing the endpoints' order in the YAML never changes
        # which side gets which address.
        ordered = sorted(endpoints, key=lambda ep: (ep["device"], ep["interface"]))
        for index, ep in enumerate(ordered):
            result[(ep["device"], ep["interface"])] = nth_usable(subnet, index)

    return result


def plan_topology(topology: dict) -> PlanResult:
    validate_references(topology)

    pools = _resolve_pools(topology)
    vlan_subnets = _resolve_vlan_subnets(topology, pools)
    link_subnets = _resolve_link_subnets(topology, pools)
    link_endpoint_addresses = _resolve_link_endpoint_addresses(topology, link_subnets)
    vlan_gateways = {vid: first_usable(net) for vid, net in vlan_subnets.items()}

    all_subnets = list(vlan_subnets.values()) + list(link_subnets.values())
    address_assignments: list[tuple[str, str]] = []
    for link_name, link in topology["links"].items():
        subnet_str = str(link_subnets[link_name])
        for ep in link["endpoints"]:
            address_assignments.append((link_endpoint_addresses[(ep["device"], ep["interface"])], subnet_str))
    address_assignments += [(gw, str(vlan_subnets[vid])) for vid, gw in vlan_gateways.items()]
    validate_resolved_addressing(all_subnets, address_assignments)

    profiles = topology.get("profiles", {})
    vlans_by_site: dict[str, list[VlanDefinition]] = {}
    vlans_by_id = {}
    for vlan in topology["vlans"]:
        defn = VlanDefinition(id=vlan["id"], name=vlan["name"])
        vlans_by_site.setdefault(vlan["site"], []).append(defn)
        vlans_by_id[vlan["id"]] = vlan

    device_models: dict[str, DeviceConfigModel] = {}
    ospf_cfg = topology["routing"]["ospf"]

    for dev_name, dev in topology["devices"].items():
        interfaces: list[ResolvedInterface] = []
        ospf_networks: list[OspfNetwork] = []

        for if_name, iface in dev["interfaces"].items():
            link_name = iface.get("link")
            mode = iface.get("mode", "routed")
            description = iface.get("description")

            if link_name is not None:
                subnet = link_subnets[link_name]
                address = link_endpoint_addresses[(dev_name, if_name)]
                other = next(
                    ep for ep in topology["links"][link_name]["endpoints"]
                    if not (ep["device"] == dev_name and ep["interface"] == if_name)
                )
                if description is None:
                    description = f"to {other['device']} {other['interface']}"
                interfaces.append(
                    ResolvedInterface(
                        name=if_name,
                        mode="routed",
                        description=description,
                        address=address,
                        prefix_length=subnet.prefixlen,
                    )
                )
                ospf_networks.append(
                    OspfNetwork(address=str(subnet.network_address), wildcard=str(subnet.hostmask), area=ospf_cfg["default_area"])
                )
            elif mode == "trunk":
                interfaces.append(
                    ResolvedInterface(
                        name=if_name,
                        mode="trunk",
                        description=description,
                        allowed_vlans=tuple(sorted(iface.get("allowed_vlans", []))),
                    )
                )
            elif mode == "access":
                interfaces.append(
                    ResolvedInterface(
                        name=if_name,
                        mode="access",
                        description=description,
                        access_vlan=iface.get("access_vlan"),
                    )
                )
            else:
                interfaces.append(ResolvedInterface(name=if_name, mode="routed", description=description))

        # VLAN gateway subinterfaces/SVIs hosted on this device.
        for vlan in topology["vlans"]:
            gateway = vlan.get("gateway")
            if gateway is None or gateway["device"] != dev_name:
                continue
            subnet = vlan_subnets[vlan["id"]]
            interfaces.append(
                ResolvedInterface(
                    name=gateway["interface"],
                    mode="routed",
                    description=f"Gateway for VLAN {vlan['id']} ({vlan['name']})",
                    address=vlan_gateways[vlan["id"]],
                    prefix_length=subnet.prefixlen,
                )
            )
            ospf_networks.append(
                OspfNetwork(address=str(subnet.network_address), wildcard=str(subnet.hostmask), area=ospf_cfg["default_area"])
            )

        interfaces.sort(key=lambda i: i.name)
        ospf_networks = sorted(set(ospf_networks), key=lambda n: (n.address, n.wildcard))

        ospf = None
        if dev.get("ospf_enabled", True) and ospf_networks:
            from ipaddress import IPv4Address

            # Cisco IOS's actual default (no configured `router-id`, no
            # loopback): the HIGHEST IP address among the interfaces up
            # at OSPF process start -- not the lowest. Confirmed against
            # this project's own captured `show ip ospf neighbor` output:
            # cross-referencing the real neighbor IDs against each real
            # device's known interface addresses, "highest interface IP"
            # matches all 7 directly-observable devices exactly (see
            # validation/historical-addressing.yaml and PROJECT_NOTES.md).
            candidate_addresses = [i.address for i in interfaces if i.address]
            router_id = str(max(IPv4Address(a) for a in candidate_addresses)) if candidate_addresses else None
            ospf = OspfConfig(process_id=ospf_cfg["process_id"], router_id=router_id, networks=tuple(ospf_networks))

        hardening = None
        profile_name = dev.get("hardening_profile")
        if profile_name is not None:
            profile = profiles[profile_name]
            hardening = HardeningConfig(
                service_password_encryption=profile.get("service_password_encryption", False),
                disable_http_server=profile.get("disable_http_server", False),
                logging_host=profile.get("logging_host"),
                domain_name=profile.get("domain_name"),
            )

        device_vlans = tuple(sorted(vlans_by_site.get(dev["site"], []), key=lambda v: v.id)) if dev["role"] == "switch" else ()

        device_models[dev_name] = DeviceConfigModel(
            hostname=dev_name,
            role=dev["role"],
            interfaces=tuple(interfaces),
            vlans=device_vlans,
            ospf=ospf,
            hardening=hardening,
        )

    return PlanResult(
        vlan_subnets=vlan_subnets,
        vlan_gateways=vlan_gateways,
        link_subnets=link_subnets,
        link_endpoint_addresses=link_endpoint_addresses,
        devices=device_models,
    )
