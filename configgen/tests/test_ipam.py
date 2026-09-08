from ipaddress import IPv4Network

import pytest

from avionics_configgen.ipam import (
    AllocationError,
    AllocationRequest,
    allocate_blocks,
    first_usable,
    hosts_to_prefix,
)


def test_hosts_to_prefix_matches_cisco_vlsm_examples():
    # Cisco's own VLSM documentation example: 62 hosts -> /26, etc.
    assert hosts_to_prefix(50) == 26  # 2**6-2=62 >= 50
    assert hosts_to_prefix(62) == 26
    assert hosts_to_prefix(63) == 25  # 62 < 63, needs the next size up
    assert hosts_to_prefix(2) == 30
    assert hosts_to_prefix(1) == 30
    assert hosts_to_prefix(100) == 25
    assert hosts_to_prefix(254) == 24


def test_hosts_to_prefix_rejects_invalid_input():
    with pytest.raises(ValueError):
        hosts_to_prefix(0)


def test_allocate_blocks_largest_first_lowest_available():
    pool = IPv4Network("10.10.0.0/24")
    requests = [
        AllocationRequest(key=("z",), prefix=27),  # smaller, declared first
        AllocationRequest(key=("a",), prefix=25),  # larger, declared second
    ]
    result = allocate_blocks(pool, requests)
    # Larger block must be placed first (lowest address) regardless of
    # declaration order in the input list.
    assert result[("a",)] == IPv4Network("10.10.0.0/25")
    assert result[("z",)] == IPv4Network("10.10.0.128/27")


def test_allocate_blocks_stable_tie_break_by_key():
    pool = IPv4Network("10.10.0.0/24")
    requests = [
        AllocationRequest(key=("site-b", 20), prefix=27),
        AllocationRequest(key=("site-a", 10), prefix=27),
    ]
    result = allocate_blocks(pool, requests)
    # Same size -> lower key wins the lower address, regardless of list order.
    assert result[("site-a", 10)] == IPv4Network("10.10.0.0/27")
    assert result[("site-b", 20)] == IPv4Network("10.10.0.32/27")


def test_allocate_blocks_is_independent_of_input_order():
    pool = IPv4Network("10.10.0.0/22")
    requests = [
        AllocationRequest(key=("c",), prefix=28),
        AllocationRequest(key=("a",), prefix=24),
        AllocationRequest(key=("b",), prefix=26),
    ]
    result_forward = allocate_blocks(pool, requests)
    result_reversed = allocate_blocks(pool, list(reversed(requests)))
    result_shuffled = allocate_blocks(pool, [requests[1], requests[2], requests[0]])
    assert result_forward == result_reversed == result_shuffled


def test_allocate_blocks_no_overlaps_across_many_requests():
    pool = IPv4Network("10.10.0.0/20")
    requests = [AllocationRequest(key=(i,), prefix=28) for i in range(16)]
    result = allocate_blocks(pool, requests)
    nets = list(result.values())
    for i, a in enumerate(nets):
        for b in nets[i + 1 :]:
            assert not a.overlaps(b)


def test_allocate_blocks_raises_when_pool_exhausted():
    pool = IPv4Network("10.10.0.0/28")  # only 16 addresses total
    requests = [AllocationRequest(key=("a",), prefix=25)]  # needs 128 addresses
    with pytest.raises(AllocationError):
        allocate_blocks(pool, requests)


def test_allocate_blocks_raises_when_second_request_does_not_fit():
    pool = IPv4Network("10.10.0.0/24")
    requests = [
        AllocationRequest(key=("a",), prefix=25),
        AllocationRequest(key=("b",), prefix=25),
        AllocationRequest(key=("c",), prefix=27),
    ]
    with pytest.raises(AllocationError):
        allocate_blocks(pool, requests)


def test_first_usable_is_network_address_plus_one():
    assert first_usable(IPv4Network("192.168.10.0/24")) == "192.168.10.1"
    assert first_usable(IPv4Network("10.255.0.0/30")) == "10.255.0.1"
