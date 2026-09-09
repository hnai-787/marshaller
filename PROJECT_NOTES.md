# Project Notes

## Source

Migrated from `air-university-cybersecurity-projects/projects/avionics-base-network`
into this workspace as an independent project on 2026-09-07.

## Cleanup decisions

None needed — no build output. All lab credentials in configs already use
`<LAB_SECRET>` placeholders in the source material.

## Assumptions

- Co-author "Ahmad Ali (232147)" is credited in the original docx report
  and pptx. The course-info table that used to surface this in the README
  was later removed along with other academic framing.

## Remaining work

None identified.

## 2026-09-08: Added avionics-configgen (declarative IOS config generator)

### What changed and why

The original project's 10+ devices' worth of interface/VLAN/OSPF/
hardening configuration were hand-typed in the Packet Tracer GUI. The
gap this fills: treat that same network as declarative data and generate
its configuration deterministically — the same model-driven pattern real
network-automation tooling (Ansible resource modules, Cisco NSO) uses in
production, at a deliberately small scale. Full research grounding
(NetBox/Ansible/pyATS topology modeling, Cisco's VLSM guidance, RFC 1878/
3021, Cisco NSO's service-model/service-mapping separation, Ansible
`ios_config`'s `rendered`/`diff_against: intended` modes, Batfish as a
future direction) is in `configgen/README.md`.

The new code lives entirely under `configgen/` and does not touch or
regenerate any of the original Packet Tracer evidence
(`packet-tracer/`, `screenshots/`, `configs/`, `docs/`) — those remain
the untouched historical baseline the new tool is checked against.

### Key engineering decisions and why

- **`mode: fixed` for the real network, `mode: computed` only for a
  separate synthetic demo topology.** The real network's addressing is
  flat one-VLAN-per-`/24`, not host-count-driven VLSM — reverse
  -engineering a tie-break policy just to make the allocator coincidentally
  reproduce those exact numbers would be curve-fitting, not verification
  (this is the research brief's own explicit warning, taken seriously).
  So the real topology (`topology/avionics-real.yaml`) reproduces history
  exactly via `fixed` allocation, and the VLSM allocator is separately
  proven correct against `topology/demo-vlsm-example.yaml` (synthetic,
  clearly labeled as such) plus direct unit tests on the allocator itself.
- **All IP arithmetic lives in Python (`planner.py`/`ipam.py`), never in
  a Jinja template** — templates only consume already-resolved dataclass
  values (`models.py`). This was the single most emphasized point in the
  research brief, and it's what makes "allocator bug vs. template bug"
  a distinguishable question when something looks wrong.
- **OSPF `router-id` corrected to match Cisco's actual default rule**
  (highest active interface IP, not lowest) — see "A real analytical
  correction" below.
- **VLAN 200 (Wireless Access Network) has no `gateway` device.** The
  original documentation records its subnet/gateway IP but never
  attributes it to a specific device. Rather than guessing one (which
  would also have broken the router-id verification below), the topology
  leaves it undeclared — it appears in the VLAN database of the relevant
  switch but has no synthesized SVI.

### A real analytical correction: OSPF router-id

Initially implemented `router-id` as the *lowest* active interface IP on
each device — a plausible-sounding but wrong assumption. Cross-checking
this project's own captured `show ip ospf neighbor` output (in
`configs/avionics-base-network-configs.md`) against each real device's
known interface addresses revealed the actual rule: Cisco IOS's genuine
default is the *highest* active interface IP at OSPF process start (when
no loopback or explicit `router-id` is configured). Verified against
**7 directly-observable devices** from the captured evidence:

| Device | Directly observed router-id | Its interfaces | Highest matches? |
|---|---|---|---|
| HQ-Router | 192.168.1.1 | {192.168.1.1, 10.0.0.1, 10.0.0.5, 10.0.0.9, 10.0.0.13, 10.0.0.17} | Yes |
| HQ-DistSwitch | 192.168.30.1 | {192.168.1.2, 192.168.10.1, 192.168.20.1, 192.168.30.1} | Yes |
| AMF-Router | 192.168.1.5 | {192.168.1.5, 10.0.0.6} | Yes |
| AMF-DistSwitch | 192.168.70.1 | {192.168.1.6, 192.168.40/50/60/70.1} | Yes |
| APF-Router | 192.168.1.9 | {192.168.1.9, 10.0.0.10} | Yes |
| ARF-Router | 192.168.1.13 | {192.168.1.13, 10.0.0.14} | Yes |
| MRF-Router | 192.168.1.17 | {192.168.1.17, 10.0.0.18} | Yes |

7/7 — not a coincidence. Fixed `planner.py` to use `max()` over
`IPv4Address` (not a lexicographic string comparison, which would be
wrong: `"10..." < "9..."` as strings). `APF-DistSwitch`/`ARF-DistSwitch`/
`MRF-DistSwitch`'s router-ids follow the same confirmed policy but were
never directly captured in the original documentation (only HQ's and
AMF's neighbor tables were included as examples) — `verify` and
`validation/historical-addressing.yaml` deliberately exclude those three
rather than treating a consistent prediction as a verified historical
fact.

### Two real bugs found and fixed

1. **Duplicate `interface Vlan10` stanza** — manually declaring a VLAN
   gateway interface under a device's own `interfaces` map *and* letting
   the planner synthesize the same interface from the VLAN's `gateway`
   field produced two stanzas with the same name in the rendered config.
   Found immediately while building the demo topology (before the real
   one). Fixed by removing the redundant declaration and adding a
   validator check (`validator.py`) that now rejects this combination,
   with a regression test.
2. **Missing newline between Jinja includes** — with the default
   `keep_trailing_newline=False`, each included feature template's own
   trailing newline was stripped, and `trim_blocks` then consumed the
   connecting newline in the parent template too; the two effects
   combined glued lines together (`hostname DEMO-HQ-SW1!` instead of two
   lines). Fixed by setting `keep_trailing_newline=True`.

### Verification performed

26 pytest tests (all passing): VLSM allocator unit tests checked against
Cisco's own published VLSM example values, ordering/tie-break/overlap/
capacity tests, schema and reference-validation tests (including
regression tests for both bugs above), determinism tests (byte-identical
regeneration, and identical output regardless of YAML key/list order —
actually tested by reversing dict/list order and re-running, not just
asserted), golden-file tests for 4 real devices and all 3 demo devices,
and an end-to-end test that `avionics-net verify` both matches the real
reference and correctly fails on a deliberately corrupted one (proving
the check isn't vacuous). Separately, `avionics-net verify
topology/avionics-real.yaml --reference
validation/historical-addressing.yaml` was actually run and reproduced
all 77 real captured addressing facts (20 VLAN subnets + gateways, 10
link subnets with 20 endpoint addresses, 7 directly-observed OSPF
router-ids) exactly:

```text
MATCH: all 77 historical addressing facts reproduced exactly.
```

Ruff reports zero issues on `configgen/src` and `configgen/tests`.

### Remaining work / honest limitations

See `configgen/README.md` "Limitations" — notably: no ACL/HSRP/VRRP
generation, no credential templating (deliberately, matching this
project's `<LAB_SECRET>` convention), no live-device or Packet Tracer
integration, and the three distribution switches' router-ids are a
consistent prediction, not a directly-verified historical fact.
