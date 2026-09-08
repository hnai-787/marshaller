"""Resolved, device-independent config model.

This is the intermediate structure the research brief calls for: the
allocator/planner produces these dataclasses, and the Jinja templates
only ever consume already-computed values from them. No IP arithmetic or
VLSM logic belongs in a template -- if that boundary is crossed, a
template bug and an allocator bug become indistinguishable.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResolvedInterface:
    name: str
    mode: str  # "routed" | "trunk" | "access"
    description: str | None = None
    address: str | None = None
    prefix_length: int | None = None
    allowed_vlans: tuple[int, ...] = ()
    access_vlan: int | None = None


@dataclass(frozen=True)
class OspfNetwork:
    address: str
    wildcard: str
    area: int


@dataclass(frozen=True)
class OspfConfig:
    process_id: int
    router_id: str
    networks: tuple[OspfNetwork, ...] = ()


@dataclass(frozen=True)
class VlanDefinition:
    id: int
    name: str


@dataclass(frozen=True)
class HardeningConfig:
    service_password_encryption: bool = False
    disable_http_server: bool = False
    logging_host: str | None = None
    domain_name: str | None = None


@dataclass(frozen=True)
class DeviceConfigModel:
    hostname: str
    role: str  # "router" | "switch"
    interfaces: tuple[ResolvedInterface, ...] = field(default_factory=tuple)
    vlans: tuple[VlanDefinition, ...] = field(default_factory=tuple)
    ospf: OspfConfig | None = None
    hardening: HardeningConfig | None = None
