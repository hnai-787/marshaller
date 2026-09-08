# avionics-configgen

A declarative Cisco IOS configuration generator built on top of this
project's real, already-verified network. It turns a YAML topology
(sites, devices, VLANs, links, routing) into per-device IOS configuration
text through a deterministic pipeline:

```text
declarative topology (YAML)
        |
    schema + reference validation
        |
    IP planning (VLSM allocator, or exact historical reproduction)
        |
    device-independent resolved model (dataclasses)
        |
    feature-specific Jinja templates
        |
    Cisco IOS configuration text
```

This mirrors the same model-driven pattern used by production network
automation (Ansible's declarative resource modules, Cisco NSO's
service-model/service-mapping split) at a deliberately small scale — see
`PROJECT_NOTES.md` in the parent project for the research this was built
from and why each design choice was made.

## Why this exists

The original Packet Tracer project's 10+ devices' worth of interface,
VLAN, OSPF, and hardening configuration were typed by hand in the Packet
Tracer GUI. This tool treats that same network as *data* instead, and
proves the treatment is faithful by regenerating the real addressing
facts this project already captured and verified — not by inventing new
ones.

## Two topologies, two different jobs

- **`topology/avionics-real.yaml`** — the real network from
  `../configs/avionics-base-network-configs.md`, transcribed with
  `allocation.mode: fixed` everywhere. This is what `verify` checks
  against `validation/historical-addressing.yaml`. It does **not**
  exercise the VLSM allocator, deliberately: the original addressing
  was flat one-VLAN-per-`/24`, not host-count-driven VLSM, so running it
  through the allocator would just be curve-fitting a policy onto numbers
  it didn't actually produce.
- **`topology/demo-vlsm-example.yaml`** — a small, clearly synthetic
  topology (says so in its own header comment) that exercises
  `allocation.mode: computed` end to end: three differently-sized VLANs
  on one pool (proving largest-first VLSM ordering) and a point-to-point
  link on a separate pool.

## Usage

```bash
pip install -e ".[dev]"

avionics-net validate topology/avionics-real.yaml
avionics-net plan topology/avionics-real.yaml
avionics-net generate topology/avionics-real.yaml --output generated/
avionics-net verify topology/avionics-real.yaml --reference validation/historical-addressing.yaml
```

## Running the tests

```bash
pytest -q
ruff check src tests
```

## Design decisions worth knowing

- **VLSM policy is this generator's own documented policy, not a
  universal standard**: requests are sized by required host count
  (smallest prefix P where `2**(32-P) - 2 >= hosts_required`), sorted
  largest-block-first, tied broken by an explicit `(site, id)` or
  link-name key (never dict/YAML order), and each gets the lowest
  available non-overlapping CIDR-aligned block via
  `ipaddress.Network.subnets()`. See `ipam.py`'s module docstring.
- **All IP arithmetic lives in Python, never in a Jinja template** — the
  planner (`planner.py`) produces fully-resolved dataclasses
  (`models.py`); templates only format already-computed values. This is
  the single boundary that makes "is this wrong because of the allocator
  or the template" a answerable question.
- **Point-to-point endpoint addresses**: for `mode: fixed` links, each
  endpoint carries its own explicit `address` (which side owns which
  address isn't derivable from the subnet alone, and guessing wrong would
  silently swap two real routers' addresses). For `mode: computed` links,
  endpoints are sorted canonically by `(device, interface)` so reversing
  their order in the YAML never changes the result — see
  `tests/test_determinism.py::test_reversing_link_endpoint_order_does_not_change_addresses`.
- **OSPF `router-id` uses Cisco's actual default rule** — the highest
  active interface IP at process start, not the lowest, and not an
  arbitrary choice. This was corrected after cross-referencing this
  project's own captured `show ip ospf neighbor` output against the real
  interface addresses: 7 of the 11 devices' router-ids are directly
  observable in the captured evidence, and "highest interface IP" matches
  all 7 exactly. See `PROJECT_NOTES.md` for the full derivation.
- **Credentials are never templated.** `hardening.j2` renders only
  non-secret toggles (`service password-encryption`, HTTP server
  disable, syslog host, domain name) from the resolved model. `enable
  secret`, SSH usernames, and banners are deliberately NOT generated —
  those need real secret values this tool has no business inventing or
  storing, matching this workspace's non-fabrication rule and the
  original project's own `<LAB_SECRET>` placeholder convention.
- **Determinism contract**: for a fixed topology, `generate` produces
  byte-identical output across runs and regardless of YAML key/list
  ordering — enforced by `tests/test_determinism.py`, not just claimed.

## Verification performed

- 26 automated tests (`pytest -q`, all passing): VLSM allocator unit
  tests (sizing against Cisco's own VLSM example values, largest-first
  ordering, stable tie-breaking, overlap/capacity errors, order
  -independence), schema and reference-validation tests (including a
  regression test for the exact duplicate-interface bug described
  below), determinism tests, golden-file regression tests for 4 real
  devices and all 3 demo devices, and an end-to-end historical
  -verification test.
- `avionics-net verify topology/avionics-real.yaml --reference
  validation/historical-addressing.yaml` reproduces **all 77** real,
  captured addressing facts (20 VLAN subnets + gateways, 10 link subnets
  with 20 endpoint addresses, 7 directly-observed OSPF router-ids)
  exactly — output is reproduced verbatim in the parent project's
  `PROJECT_NOTES.md`.
- Ruff reports zero issues on `src/` and `tests/`.

## Two real bugs found while building this (not hidden)

1. **Duplicate interface stanza.** Manually declaring a VLAN's gateway
   interface (e.g. `Vlan10`) under a device's own `interfaces` map *and*
   letting the planner synthesize the same interface from the VLAN's
   `gateway` field produced two `interface Vlan10` stanzas in the
   rendered config. Fixed two ways: removed the redundant declaration
   from the demo topology, and added a validator check
   (`validator.py::validate_references`) that now rejects this
   combination outright, with a regression test.
2. **Missing newline between included templates.** With Jinja's
   `keep_trailing_newline=False` (the default), each included
   feature-template's own trailing newline was stripped, and
   `trim_blocks` then ate the connecting newline in the parent template
   — the two effects combined to glue lines together
   (`hostname DEMO-HQ-SW1!` instead of two separate lines). Fixed by
   setting `keep_trailing_newline=True` in the renderer's `Environment`.

## Limitations

- Covers interfaces, VLANs, trunking (schema-supported, not exercised by
  either topology here since neither needs access-layer trunk ports),
  OSPF, and non-secret hardening. Does not generate ACLs, HSRP/VRRP, or
  anything credential-bearing.
- `APF-DistSwitch`/`ARF-DistSwitch`/`MRF-DistSwitch`'s predicted
  router-ids are consistent with the confirmed policy but were never
  directly captured in the original documentation — `verify` deliberately
  excludes them rather than treating a prediction as a verified fact.
- No live device or Packet Tracer integration — this generates config
  text only; nothing here re-runs the original simulation.

## Future Enhancements

- pyATS/Genie-based operational-state validation against a live CML or
  real IOS lab, per the research this was built from.
- Batfish-based offline reachability/policy analysis as a stronger
  pre-deployment check than text/semantic diffing alone.
