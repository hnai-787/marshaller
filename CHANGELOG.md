# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

### Changed

### Fixed

- README's Repository Structure still said `avionics-base-network/` from
  before the product-name rebrand; corrected to `marshaller/`.
- README's Repository Structure and "How to Review" still referenced
  `docs/avionics-base-network-report.docx` and
  `presentation/avionics-base-network-presentation.pptx`, both of which
  were removed from this repository earlier in this project's history
  (they named a real collaborator); replaced with an accurate note that
  they're archived outside this repository.

## [1.1.0] - 2026-09-08

### Added

- **`configgen/`**: a new declarative Cisco IOS configuration generator.
  YAML topology (address pools, sites, devices, VLANs, links, routing) ->
  schema + reference validation -> a deterministic largest-first VLSM
  IP planner (`ipam.py`) -> a device-independent resolved config model
  (`models.py`) -> feature-specific Jinja templates -> IOS config text.
- `topology/avionics-real.yaml`: the real network transcribed with exact
  historical addressing (`allocation.mode: fixed` throughout).
- `topology/demo-vlsm-example.yaml`: a synthetic topology exercising the
  VLSM allocator (`allocation.mode: computed`) end to end.
- `validation/historical-addressing.yaml` and the `avionics-net verify`
  command: reproduces all 77 of this network's real, previously-captured
  addressing facts (20 VLAN subnets + gateways, 10 link subnets with 20
  endpoint addresses, 7 directly-observed OSPF router-ids) exactly.
- 26 pytest tests: VLSM allocator correctness (checked against Cisco's
  own published VLSM example values), schema/reference validation,
  determinism (byte-identical regeneration, order-independence), golden
  -file regression, and end-to-end historical verification.
- `.github/workflows/configgen-ci.yml`: Ruff + pytest + regenerate +
  verify, triggered on changes under `configgen/`, actions pinned to
  commit SHAs.

### Changed

- `project.yaml`: `portfolio.featured` set to `true`.

### Fixed

- (within `configgen`, new code — not a fix to the original project)
  a duplicate `interface Vlan10` stanza caused by declaring a VLAN
  gateway interface both manually and via auto-synthesis, and a Jinja
  whitespace bug that glued `hostname X` directly onto the following
  line with no newline between them. See `PROJECT_NOTES.md` for both.
