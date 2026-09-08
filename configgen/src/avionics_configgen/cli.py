"""Command-line entry point: validate / plan / generate / verify."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .loader import TopologyLoadError, load_topology
from .planner import plan_topology
from .renderer import render_device
from .validator import TopologyValidationError


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        topology = load_topology(args.topology)
        plan_topology(topology)
    except (TopologyLoadError, TopologyValidationError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print("OK: topology is valid and fully resolvable.")
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    topology = load_topology(args.topology)
    result = plan_topology(topology)

    print("ADDRESS PLAN")
    print("============")
    print()
    print("VLANs")
    print("-----")
    for vlan in sorted(topology["vlans"], key=lambda v: v["id"]):
        subnet = result.vlan_subnets[vlan["id"]]
        gateway = result.vlan_gateways[vlan["id"]]
        print(f"{vlan['site']} / {vlan['name']} / VLAN {vlan['id']}")
        print(f"  {subnet}  gateway {gateway}  ({subnet.num_addresses - 2} usable)")
    print()
    print("LINKS")
    print("-----")
    for link_name in sorted(topology["links"]):
        subnet = result.link_subnets[link_name]
        print(f"{link_name}: {subnet}")
        for ep in topology["links"][link_name]["endpoints"]:
            addr = result.link_endpoint_addresses[(ep["device"], ep["interface"])]
            print(f"  {ep['device']} {ep['interface']} = {addr}")
    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    topology = load_topology(args.topology)
    result = plan_topology(topology)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, model in sorted(result.devices.items()):
        text = render_device(model)
        out_path = out_dir / f"{name}.cfg"
        out_path.write_bytes(text.encode("utf-8"))
        print(f"wrote {out_path}")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    topology = load_topology(args.topology)
    result = plan_topology(topology)

    with open(args.reference, encoding="utf-8") as f:
        reference = yaml.safe_load(f)

    mismatches: list[str] = []

    for vlan_id_str, expected in reference.get("vlans", {}).items():
        vlan_id = int(vlan_id_str)
        actual_subnet = str(result.vlan_subnets.get(vlan_id))
        actual_gateway = result.vlan_gateways.get(vlan_id)
        if actual_subnet != expected["subnet"]:
            mismatches.append(f"VLAN {vlan_id} subnet: expected {expected['subnet']}, got {actual_subnet}")
        if actual_gateway != expected["gateway"]:
            mismatches.append(f"VLAN {vlan_id} gateway: expected {expected['gateway']}, got {actual_gateway}")

    for link_name, expected in reference.get("links", {}).items():
        actual_subnet = str(result.link_subnets.get(link_name))
        if actual_subnet != expected["subnet"]:
            mismatches.append(f"link {link_name} subnet: expected {expected['subnet']}, got {actual_subnet}")
        for ep_key, expected_addr in expected.get("endpoints", {}).items():
            device, interface = ep_key.split("::", 1)
            actual_addr = result.link_endpoint_addresses.get((device, interface))
            if actual_addr != expected_addr:
                mismatches.append(
                    f"link {link_name} endpoint {device}/{interface}: expected {expected_addr}, got {actual_addr}"
                )

    for device_name, expected in reference.get("routers", {}).items():
        model = result.devices.get(device_name)
        actual_router_id = model.ospf.router_id if model and model.ospf else None
        if actual_router_id != expected["router_id"]:
            mismatches.append(
                f"router-id {device_name}: expected {expected['router_id']}, got {actual_router_id}"
            )

    total_checks = (
        sum(2 for _ in reference.get("vlans", {}))
        + sum(1 + len(v.get("endpoints", {})) for v in reference.get("links", {}).values())
        + len(reference.get("routers", {}))
    )

    if mismatches:
        print(f"MISMATCH ({len(mismatches)} of {total_checks} checks failed):")
        for m in mismatches:
            print(f"  - {m}")
        return 1

    print(f"MATCH: all {total_checks} historical addressing facts reproduced exactly.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="avionics-net")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="validate a topology file")
    p_validate.add_argument("topology")
    p_validate.set_defaults(func=_cmd_validate)

    p_plan = sub.add_parser("plan", help="print the resolved address plan")
    p_plan.add_argument("topology")
    p_plan.set_defaults(func=_cmd_plan)

    p_generate = sub.add_parser("generate", help="generate per-device IOS configs")
    p_generate.add_argument("topology")
    p_generate.add_argument("--output", default="generated")
    p_generate.set_defaults(func=_cmd_generate)

    p_verify = sub.add_parser("verify", help="compare resolved facts against a historical reference")
    p_verify.add_argument("topology")
    p_verify.add_argument("--reference", required=True)
    p_verify.set_defaults(func=_cmd_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
