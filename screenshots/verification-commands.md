# Verification Commands

This file records the main CLI and client-side verification evidence for the Multi-Site Aviation Campus Network Simulation.

## HQ Distribution Switch VLAN Verification

```text
HQ-DIST-SW#show vlan brief

VLAN Name                             Status
---- -------------------------------- ---------
1    default                          active
10   VLAN10                           active
20   VLAN20                           active
30   VLAN30                           active
```

## HQ Distribution Switch Interface Verification

```text
HQ-DIST-SW#show ip interface brief

Interface              IP-Address      Status                Protocol
GigabitEthernet1/0/1   192.168.1.2     up                    up
Vlan10                 192.168.10.1    up                    up
Vlan20                 192.168.20.1    up                    up
Vlan30                 192.168.30.1    up                    up
```

## HQ Data Center Access Switch VLAN Verification

```text
HQ-ACCESS-SW-DC>show vlan brief

VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
10   VLAN10                           active    Fa0/1, Fa0/2, Fa0/3, Fa0/4
                                                Fa0/5, Fa0/6, Fa0/7, Fa0/8
                                                Fa0/9, Fa0/10, Fa0/11, Fa0/12
                                                Fa0/13, Fa0/14, Fa0/15, Fa0/16
                                                Fa0/17, Fa0/18, Fa0/19, Fa0/20
                                                Fa0/21, Fa0/22, Fa0/23, Fa0/24
```

## AMF Distribution Switch VLAN and Trunk Verification

```text
AMF-DIST-SW#show vlan brief

VLAN Name                             Status
---- -------------------------------- ---------
40   VLAN40                           active
50   VLAN50                           active
60   VLAN60                           active
70   VLAN70                           active
```

```text
AMF-DIST-SW#show interfaces trunk

Port        Vlans allowed and active in management domain
Gig1/0/2    1,40,50,60,70
Gig1/0/3    1,40,50,60,70
Gig1/0/4    1,40,50,60,70
Gig1/0/5    1,40,50,60,70
```

## APF Distribution Switch VLAN and Trunk Verification

```text
APF-DIST-SW#show vlan brief

VLAN Name                             Status
---- -------------------------------- ---------
80   VLAN80                           active
90   VLAN90                           active
100  VLAN100                          active
110  VLAN110                          active
```

```text
APF-DIST-SW#show interfaces trunk

Port        Vlans allowed and active in management domain
Gig1/0/2    1,80,90,100,110
Gig1/0/3    1,80,90,100,110
Gig1/0/4    1,80,90,100,110
Gig1/0/5    1,80,90,100,110
```

## ARF Distribution Switch VLAN and Trunk Verification

```text
ARF-Dist-SW#show vlan brief

VLAN Name                             Status
---- -------------------------------- ---------
120  VLAN0120                         active
130  VLAN0130                         active
140  VLAN0140                         active
150  VLAN0150                         active
```

```text
ARF-Dist-SW#show interfaces trunk

Port        Vlans allowed and active in management domain
Gig1/0/2    1,120,130,140,150
Gig1/0/3    1,120,130,140,150
Gig1/0/4    1,120,130,140,150
Gig1/0/5    1,120,130,140,150
```

## MRF Distribution Switch VLAN and Trunk Verification

```text
MRF-DIST-SW#show vlan brief

VLAN Name                             Status
---- -------------------------------- ---------
160  VLAN0160                         active
170  VLAN0170                         active
180  VLAN0180                         active
190  VLAN0190                         active
```

```text
MRF-DIST-SW#show interfaces trunk

Port        Vlans allowed and active in management domain
Gig1/0/2    1,160,170,180,190
Gig1/0/3    1,160,170,180,190
Gig1/0/4    1,160,170,180,190
Gig1/0/5    1,160,170,180,190
```

## HQ Router OSPF Verification

```text
HQ-RTR#show ip ospf neighbor

Neighbor ID     Pri   State           Dead Time   Address         Interface
192.168.30.1      1   FULL/DR         00:00:30    192.168.1.2     GigabitEthernet0/0
192.168.1.5       0   FULL/  -        00:00:39    10.0.0.6        Serial0/0/0
192.168.1.9       0   FULL/  -        00:00:30    10.0.0.10       Serial0/0/1
192.168.1.13      0   FULL/  -        00:00:32    10.0.0.14       Serial0/1/0
192.168.1.17      0   FULL/  -        00:00:30    10.0.0.18       Serial0/1/1
```

## AMF Router Route Verification

```text
AMF-RTR#show ip route

Gateway of last resort is not set

     10.0.0.0/8 is variably subnetted, 6 subnets, 2 masks
O       10.0.0.0/30 [110/65] via 10.0.0.5, Serial0/0/0
C       10.0.0.4/30 is directly connected, Serial0/0/0
L       10.0.0.6/32 is directly connected, Serial0/0/0
O       10.0.0.8/30 [110/128] via 10.0.0.5, Serial0/0/0
O       10.0.0.12/30 [110/128] via 10.0.0.5, Serial0/0/0
O       10.0.0.16/30 [110/128] via 10.0.0.5, Serial0/0/0
     192.168.1.0/24 is variably subnetted, 6 subnets, 2 masks
O       192.168.1.0/30 [110/65] via 10.0.0.5, Serial0/0/0
C       192.168.1.4/30 is directly connected, GigabitEthernet0/0
L       192.168.1.5/32 is directly connected, GigabitEthernet0/0
O       192.168.1.8/30 [110/129] via 10.0.0.5, Serial0/0/0
```

## AMF Router Interface Verification

```text
AMF-RTR#show ip interface brief

Interface              IP-Address      Status                Protocol
GigabitEthernet0/0     192.168.1.5     up                    up
Serial0/0/0            10.0.0.6        up                    up
```

## AMF Router OSPF Neighbor Verification

```text
AMF-RTR#show ip ospf neighbor

Neighbor ID     Pri   State           Dead Time   Address         Interface
192.168.70.1      1   FULL/DR         00:00:35    192.168.1.6     GigabitEthernet0/0
192.168.1.1       0   FULL/  -        00:00:34    10.0.0.5        Serial0/0/0
```

## Factory PC Service Reachability Test

```text
C:\>ping 192.168.10.10
Reply from 192.168.10.10: bytes=32 time=46ms TTL=124
Reply from 192.168.10.10: bytes=32 time=19ms TTL=124

C:\>ping 192.168.10.11
Reply from 192.168.10.11: bytes=32 time=1ms TTL=124
Reply from 192.168.10.11: bytes=32 time=16ms TTL=124
Reply from 192.168.10.11: bytes=32 time=97ms TTL=124
Reply from 192.168.10.11: bytes=32 time=24ms TTL=124

C:\>ping 192.168.10.12
Reply from 192.168.10.12: bytes=32 time=26ms TTL=124
Reply from 192.168.10.12: bytes=32 time=18ms TTL=124
Reply from 192.168.10.12: bytes=32 time=42ms TTL=124
Reply from 192.168.10.12: bytes=32 time=11ms TTL=124

C:\>ping 192.168.10.13
Reply from 192.168.10.13: bytes=32 time=46ms TTL=124
Reply from 192.168.10.13: bytes=32 time=21ms TTL=124
Reply from 192.168.10.13: bytes=32 time=2ms TTL=124
Reply from 192.168.10.13: bytes=32 time=16ms TTL=124
```

## Factory PC DNS Name Resolution Test

```text
C:\>ping www.aoh.com
Pinging 192.168.10.13 with 32 bytes of data:
Reply from 192.168.10.13: bytes=32 time=36ms TTL=124
Reply from 192.168.10.13: bytes=32 time=63ms TTL=124
Reply from 192.168.10.13: bytes=32 time=10ms TTL=124
Reply from 192.168.10.13: bytes=32 time=12ms TTL=124

C:\>ping mail.aoh.com
Pinging 192.168.10.11 with 32 bytes of data:
Reply from 192.168.10.11: bytes=32 time=25ms TTL=124
Reply from 192.168.10.11: bytes=32 time=22ms TTL=124
Reply from 192.168.10.11: bytes=32 time=13ms TTL=124
Reply from 192.168.10.11: bytes=32 time=13ms TTL=124

C:\>ping ftp.aoh.com
Pinging 192.168.10.12 with 32 bytes of data:
Reply from 192.168.10.12: bytes=32 time=31ms TTL=124
Reply from 192.168.10.12: bytes=32 time=11ms TTL=124
Reply from 192.168.10.12: bytes=32 time=58ms TTL=124
Reply from 192.168.10.12: bytes=32 time=33ms TTL=124
```

## Notes

The first DNS server ping had initial packet loss before later replies. In Packet Tracer, this can happen due to ARP resolution or simulation convergence. DNS functionality is confirmed by successful resolution of `www.aoh.com`, `mail.aoh.com`, and `ftp.aoh.com`.
