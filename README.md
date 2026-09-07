# Avionics Base Network Simulation

## Course Information

| Field | Details |
|---|---|
| Course | Computer Networks Lab (CS260L) |
| Semester | Semester 3 — Fall 2024 |
| University | Air University, Islamabad |
| Students | Hussain Ali (232095), Ahmad Ali (232147) |

## Overview

A Cisco Packet Tracer simulation of a multi-site aviation-base network: a
headquarters site connected to four factory sites via routed
point-to-point links, using OSPF for dynamic routing and department-level
VLAN segmentation.

## Problem Statement

Design and verify a realistic multi-site enterprise network — dynamic
routing between sites, VLAN segmentation within sites, and working
DNS/FTP/Web/Mail services — entirely in simulation.

## Objectives

- Connect HQ and 4 factory sites via routed point-to-point (/30) links.
- Run OSPF area 0 across all routers for dynamic routing.
- Segment ~20 departments into VLANs on separate /24 subnets.
- Verify DNS, FTP, Web, and Mail service reachability from factory sites.

## Tools and Technologies

- Cisco Packet Tracer
- OSPF (area 0)
- VLANs, 802.1Q trunking
- Cisco IOS CLI

## Features

- HQ site: firewall, main router, distribution switch, DNS/FTP/Web/Mail servers.
- 4 factory sites (AMF, APF, ARF, MRF) each routed to HQ.
- ~20 VLANs across 192.168.10.0/24–200.0/24.
- Verified OSPF adjacencies and end-to-end service reachability.

## Methodology

1. Design the logical topology (HQ + 4 factory sites, routed links, OSPF area 0).
2. Configure VLANs and trunking within each site.
3. Configure OSPF on all routers and verify neighbor adjacency.
4. Verify DNS resolution and FTP/Web/Mail reachability from each factory site.

## Repository Structure

```text
avionics-base-network/
  README.md
  PROJECT_NOTES.md
  packet-tracer/avionics-base-network-simulation.pkt
  configs/avionics-base-network-configs.md
  screenshots/verification-commands.md
  topology/logical-diagram.png
  docs/avionics-base-network-report.docx
  presentation/avionics-base-network-presentation.pptx
  screenshots/
  project.yaml
```

## Setup Instructions

Open `packet-tracer/avionics-base-network-simulation.pkt` in Cisco Packet Tracer.

## Usage

Use Packet Tracer's simulation mode to trace OSPF hellos/adjacencies and
test connectivity (ping, DNS lookups, FTP/web/mail access) between sites.

## How to Review

1. Start with this README, then `docs/avionics-base-network-report.docx`.
2. Review `topology/logical-diagram.png` for the overall design.
3. Check `configs/avionics-base-network-configs.md` and `screenshots/verification-commands.md` for real verification command output.
4. Open the `.pkt` file to explore the live simulation.

## Screenshots

See `screenshots/` (7 images) and `topology/logical-diagram.png`.

## Results

Real, captured verification output: all OSPF neighbor adjacencies reached
`FULL` state; VLAN/trunk configuration verified via `show` commands;
factory-site pings to DNS/Mail/FTP/Web servers all succeeded (1–97ms
response times), and DNS correctly resolved `www.aoh.com`, `mail.aoh.com`,
and `ftp.aoh.com`. All lab credentials shown in configs use `<LAB_SECRET>`
placeholders.

## Limitations

- Simulation only (Packet Tracer) — not tested against real hardware.
- No redundancy/failover paths between HQ and factory sites.

## Future Enhancements

- Add redundant links and HSRP/VRRP for gateway failover.
- Add ACLs to enforce inter-VLAN security policy explicitly.

## Safety and Privacy

- No real secrets or credentials — all shown values use `<LAB_SECRET>` placeholders.
- Purely a simulation; no real network or organization is involved.

## Ethical Notice

Academic coursework exercise; no ethical concerns apply.
