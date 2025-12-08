# dec/08/2025 10:03:38 by RouterOS 6.49.13
# software id = V49E-2TJP
#
# model = RB941-2nD
# serial number = HGA09V8VP2Y
/interface bridge
add admin-mac=D4:01:C3:6F:3F:01 auto-mac=no comment=defconf name=bridgeLocal
/interface wireless
# managed by CAPsMAN
set [ find default-name=wlan1 ] ssid=MikroTik
/interface wireless security-profiles
set [ find default=yes ] supplicant-identity=MikroTik
/ip hotspot profile
add dns-name=google.com hotspot-address=192.168.1.159 name=hsprof1
/ip hotspot user profile
add name=daily_1000 rate-limit=1M/1M session-timeout=1d
add name=monthly_1000 rate-limit=1M/1M session-timeout=4w2d
/ip pool
add name=hs-pool-7 ranges=\
    192.168.1.1-192.168.1.158,192.168.1.160-192.168.1.254
/ip dhcp-server
add address-pool=hs-pool-7 disabled=no interface=bridgeLocal lease-time=1h \
    name=dhcp1
/ip hotspot
add address-pool=hs-pool-7 disabled=no interface=bridgeLocal name=hotspot1 \
    profile=hsprof1
/interface bridge port
add bridge=bridgeLocal comment=defconf interface=ether1
add bridge=bridgeLocal comment=defconf interface=ether2
add bridge=bridgeLocal comment=defconf interface=ether3
add bridge=bridgeLocal comment=defconf interface=ether4
/interface wireless cap
# 
set bridge=bridgeLocal discovery-interfaces=bridgeLocal enabled=yes \
    interfaces=wlan1
/ip dhcp-client
add comment=defconf disabled=no interface=bridgeLocal
/ip dhcp-server network
add address=192.168.1.0/24 comment="hotspot network" gateway=192.168.1.159
/ip dns
set servers=8.8.8.8
/ip firewall filter
add action=passthrough chain=unused-hs-chain comment=\
    "place hotspot rules here" disabled=yes
/ip firewall nat
add action=passthrough chain=unused-hs-chain comment=\
    "place hotspot rules here" disabled=yes
add action=masquerade chain=srcnat comment="masquerade hotspot network" \
    src-address=192.168.1.0/24
/ip hotspot user
add name=admin password=jelius
/system clock
set time-zone-name=Africa/Dar_es_Salaam
