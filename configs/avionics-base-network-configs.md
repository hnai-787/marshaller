# Avionics Base Network Configuration Notes

## Overview

This document summarizes the final configuration design and verification evidence for the Multi-Site Aviation Campus Network Simulation.

The Packet Tracer file keeps some original device/VLAN labels, but the public documentation presents the project as a fictional academic aviation-campus network.

> Public repository note: do not expose real or reused passwords. Use `<LAB_SECRET>` for credentials in public documentation.

## 1. Service Addressing

| Service | DNS Name | IP Address | Network |
|---|---|---:|---|
| DNS | `dns.aoh.com` | `192.168.10.10` | HQ Data Center |
| Mail | `mail.aoh.com` | `192.168.10.11` | HQ Data Center |
| FTP | `ftp.aoh.com` | `192.168.10.12` | HQ Data Center |
| Web | `www.aoh.com` | `192.168.10.13` | HQ Data Center |
| Syslog | `syslog.aoh.com` | `192.168.30.10` | HQ SOC |

DNS records verified in Packet Tracer:

```text
dns.aoh.com      192.168.10.10
mail.aoh.com     192.168.10.11
ftp.aoh.com      192.168.10.12
www.aoh.com      192.168.10.13
syslog.aoh.com   192.168.30.10
```

## 2. VLAN Gateway Addressing

| VLAN | Gateway IP Address | Intended Segment |
|---:|---|---|
| 10 | 192.168.10.1 | HQ Data Center |
| 20 | 192.168.20.1 | HQ Control Center |
| 30 | 192.168.30.1 | HQ SOC |
| 40 | 192.168.40.1 | AMF Design and Development |
| 50 | 192.168.50.1 | AMF Prototyping and Testing |
| 60 | 192.168.60.1 | AMF Quality Control |
| 70 | 192.168.70.1 | AMF Support Services |
| 80 | 192.168.80.1 | APF Avionics Design |
| 90 | 192.168.90.1 | APF Production |
| 100 | 192.168.100.1 | APF Testing and Calibration |
| 110 | 192.168.110.1 | APF Support Services |
| 120 | 192.168.120.1 | ARF Overhaul Division |
| 130 | 192.168.130.1 | ARF Repair Division |
| 140 | 192.168.140.1 | ARF Testing and Certification |
| 150 | 192.168.150.1 | ARF Support Services |
| 160 | 192.168.160.1 | MRF Overhaul Division |
| 170 | 192.168.170.1 | MRF Repair Division |
| 180 | 192.168.180.1 | MRF Testing Division |
| 190 | 192.168.190.1 | MRF Support Services |
| 200 | 192.168.200.1 | Wireless Access Network |

## 3. Point-to-Point Link Addressing

| Link | Subnet ID | Usable IPs | Broadcast Address |
|---|---|---|---|
| Firewall to HQ Router | 10.0.0.0/30 | 10.0.0.1, 10.0.0.2 | 10.0.0.3 |
| HQ Router to AMF Router | 10.0.0.4/30 | 10.0.0.5, 10.0.0.6 | 10.0.0.7 |
| HQ Router to APF Router | 10.0.0.8/30 | 10.0.0.9, 10.0.0.10 | 10.0.0.11 |
| HQ Router to ARF Router | 10.0.0.12/30 | 10.0.0.13, 10.0.0.14 | 10.0.0.15 |
| HQ Router to MRF Router | 10.0.0.16/30 | 10.0.0.17, 10.0.0.18 | 10.0.0.19 |
| HQ Router to HQ Distribution Switch | 192.168.1.0/30 | 192.168.1.1, 192.168.1.2 | 192.168.1.3 |
| AMF Router to AMF Distribution Switch | 192.168.1.4/30 | 192.168.1.5, 192.168.1.6 | 192.168.1.7 |
| APF Router to APF Distribution Switch | 192.168.1.8/30 | 192.168.1.9, 192.168.1.10 | 192.168.1.11 |
| ARF Router to ARF Distribution Switch | 192.168.1.12/30 | 192.168.1.13, 192.168.1.14 | 192.168.1.15 |
| MRF Router to MRF Distribution Switch | 192.168.1.16/30 | 192.168.1.17, 192.168.1.18 | 192.168.1.19 |

## 4. VLAN and Trunk Verification Summary

Verified VLAN ranges:

```text
HQ:  VLAN 10, 20, 30
AMF: VLAN 40, 50, 60, 70
APF: VLAN 80, 90, 100, 110
ARF: VLAN 120, 130, 140, 150
MRF: VLAN 160, 170, 180, 190
```

Facility trunk verification showed the correct VLANs active and forwarding on distribution-switch trunk ports.

Example APF trunk output summary:

```text
Gig1/0/2    1,80,90,100,110
Gig1/0/3    1,80,90,100,110
Gig1/0/4    1,80,90,100,110
Gig1/0/5    1,80,90,100,110
```

Example AMF trunk output summary:

```text
Gig1/0/2    1,40,50,60,70
Gig1/0/3    1,40,50,60,70
Gig1/0/4    1,40,50,60,70
Gig1/0/5    1,40,50,60,70
```

## 5. OSPF Routing Verification

### HQ Router OSPF Neighbors

The HQ router formed OSPF FULL adjacencies with HQ distribution and all facility routers:

```text
Neighbor ID     State      Address       Interface
192.168.30.1    FULL/DR    192.168.1.2   GigabitEthernet0/0
192.168.1.5     FULL/-     10.0.0.6      Serial0/0/0
192.168.1.9     FULL/-     10.0.0.10     Serial0/0/1
192.168.1.13    FULL/-     10.0.0.14     Serial0/1/0
192.168.1.17    FULL/-     10.0.0.18     Serial0/1/1
```

### AMF Router OSPF Neighbors

AMF router formed OSPF FULL adjacencies with the AMF distribution switch and HQ router:

```text
Neighbor ID     State      Address       Interface
192.168.70.1    FULL/DR    192.168.1.6   GigabitEthernet0/0
192.168.1.1     FULL/-     10.0.0.5      Serial0/0/0
```

## 6. Example Router Interfaces

### HQ Router

```text
GigabitEthernet0/0     192.168.1.1     up/up
GigabitEthernet0/1     10.0.0.1        up/up
Serial0/0/0            10.0.0.5        up/up
Serial0/0/1            10.0.0.9        up/up
Serial0/1/0            10.0.0.13       up/up
Serial0/1/1            10.0.0.17       up/up
```

### AMF Router

```text
GigabitEthernet0/0     192.168.1.5     up/up
Serial0/0/0            10.0.0.6        up/up
```

## 7. Service Reachability Verification

A factory PC successfully reached the HQ-hosted services:

```text
ping 192.168.10.10    DNS Server
ping 192.168.10.11    Mail Server
ping 192.168.10.12    FTP Server
ping 192.168.10.13    Web Server
ping www.aoh.com      Web DNS resolution
ping mail.aoh.com     Mail DNS resolution
ping ftp.aoh.com      FTP DNS resolution
```

DNS resolution confirmed:

```text
www.aoh.com   -> 192.168.10.13
mail.aoh.com  -> 192.168.10.11
ftp.aoh.com   -> 192.168.10.12
```

## 8. Basic Device Hardening Template

Use placeholder credentials in public documentation.

```cisco
enable
configure terminal

no ip domain-lookup
service password-encryption
ip domain-name aoh.local

enable secret <LAB_SECRET>
username netadmin privilege 15 secret <LAB_SECRET>
crypto key generate rsa modulus 1024
ip ssh version 2

banner motd #
Unauthorized access is prohibited. This device is part of an academic Packet Tracer simulation.
#

line console 0
 password <LAB_SECRET>
 login
 logging synchronous

line vty 0 4
 login local
 transport input ssh
end
write memory
```

## 9. Syslog Configuration Template

```cisco
enable
configure terminal

logging on
logging host 192.168.30.10
logging trap debugging
logging console
logging userinfo

end
write memory
```

## 10. Useful Verification Commands

```cisco
show vlan brief
show interfaces trunk
show ip interface brief
show ip route
show ip ospf neighbor
show running-config
show logging
```

## 11. Documentation Notes

- The project is an academic Packet Tracer simulation.
- VLAN names in the Packet Tracer file may use default-style labels such as `VLAN40` or `VLAN0120`; the documented tables explain the intended department mapping.
- The public GitHub version should use fictional aviation-campus wording rather than presenting the topology as a real organization or infrastructure.
- Credentials should be documented only as `<LAB_SECRET>`.
