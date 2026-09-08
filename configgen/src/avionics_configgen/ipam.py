"""Deterministic VLSM address allocation.

Policy (documented here because it is this generator's own deterministic
policy, not a universal networking standard -- see the research this was
built from):

1. Requests are sized by required host count: the smallest prefix P such
   that 2**(32-P) - 2 >= hosts_required.
2. Requests are sorted largest-block-first (prefix ascending); ties
   within the same block size are broken by an explicit, caller-supplied
   stable key (e.g. (site, vlan_id) or a link id) -- never by dict/YAML
   iteration order.
3. Each request is assigned the lowest-address CIDR-aligned block of its
   required size, within its pool, that does not overlap a block already
   allocated. `ipaddress.subnets()` enumerates candidate blocks in
   address order, so "first non-overlapping candidate" is exactly
   "lowest available block".

This makes allocation a pure function of (pool, request sizes, request
keys) -- never of dict ordering -- which is what makes regeneration
byte-identical regardless of how the topology YAML happens to order its
keys.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv4Network


class AllocationError(Exception):
    pass


def hosts_to_prefix(hosts_required: int) -> int:
    if hosts_required < 1:
        raise ValueError("hosts_required must be >= 1")
    for host_bits in range(1, 31):
        if (2**host_bits) - 2 >= hosts_required:
            return 32 - host_bits
    raise ValueError(f"hosts_required={hosts_required} is too large for IPv4")


@dataclass(frozen=True)
class AllocationRequest:
    key: tuple
    prefix: int


def allocate_blocks(pool: IPv4Network, requests: list[AllocationRequest]) -> dict[tuple, IPv4Network]:
    """Allocate one CIDR block per request from `pool`.

    Returns a mapping from each request's key to its assigned IPv4Network.
    Raises AllocationError if a request's size doesn't fit anywhere in
    the pool after prior allocations.
    """
    ordered = sorted(requests, key=lambda r: (r.prefix, r.key))

    allocated: list[IPv4Network] = []
    result: dict[tuple, IPv4Network] = {}

    for request in ordered:
        if request.prefix < pool.prefixlen:
            raise AllocationError(
                f"request {request.key} needs a /{request.prefix} block, "
                f"smaller than pool {pool} (/{pool.prefixlen})"
            )

        chosen = None
        for candidate in pool.subnets(new_prefix=request.prefix):
            if not any(candidate.overlaps(existing) for existing in allocated):
                chosen = candidate
                break

        if chosen is None:
            raise AllocationError(
                f"pool {pool} exhausted: no /{request.prefix} block available for {request.key}"
            )

        allocated.append(chosen)
        result[request.key] = chosen

    return result


def first_usable(network: IPv4Network) -> str:
    hosts = list(network.hosts())
    if not hosts:
        # /31 and /32 have no "usable hosts" in the classic sense;
        # treat network/broadcast as the two usable addresses for /31.
        if network.prefixlen == 31:
            return str(next(iter(network)))
        raise ValueError(f"{network} has no usable host addresses")
    return str(hosts[0])


def nth_usable(network: IPv4Network, index: int) -> str:
    """0-based index into the usable host addresses of `network`."""
    if network.prefixlen == 31:
        addresses = list(network)
    else:
        addresses = list(network.hosts())
    return str(addresses[index])
