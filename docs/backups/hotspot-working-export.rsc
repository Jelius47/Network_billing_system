# 2026-01-10 22:30:15 by RouterOS 7.18.2
# software id = 0FZ0-W5YV
#
# model = E60iUGS
# serial number = HJS0AHN4J20
/interface bridge
add mtu=1500 name=bridge1
/ip hotspot profile
set [ find default=yes ] login-by=cookie,http-pap
add dns-name=hotspot.com hotspot-address=192.168.88.1 login-by=\
    cookie,http-pap name=hsprof1
/ip hotspot user profile
add keepalive-timeout=1d name=Daily-1K rate-limit=4M/4M
add keepalive-timeout=4w2d name=Monthly-10K rate-limit=4M/4M
add keepalive-timeout=4w2d name=Monthly-15K rate-limit=4M/4M
/ip pool
add name=hotspot-pool ranges=192.168.88.100-192.168.88.254
/ip dhcp-server
add address-pool=hotspot-pool interface=bridge1 name=dhcp1
/ip hotspot
add address-pool=hotspot-pool disabled=no interface=bridge1 name=hotspot1 \
    profile=hsprof1
/queue type
add kind=pcq name=pcq-4mbps pcq-classifier=src-address,dst-address pcq-rate=\
    4M
add kind=pcq name=pcq-equal-4mbps pcq-classifier=src-address,dst-address \
    pcq-rate=4M
/queue tree
add max-limit=40M name=total-download parent=global queue=pcq-equal-4mbps
add max-limit=40M name=total-upload parent=ether1 queue=pcq-equal-4mbps
/interface bridge port
add bridge=bridge1 interface=ether2
add bridge=bridge1 interface=ether4
/ip neighbor discovery-settings
set discover-interface-list=!dynamic
/ip address
add address=192.168.88.1/24 interface=bridge1 network=192.168.88.0
/ip dhcp-client
add interface=ether1
/ip dhcp-server network
add address=192.168.88.0/24 dns-server=8.8.8.8,1.1.1.1 gateway=192.168.88.1
/ip dns
set allow-remote-requests=yes servers=8.8.8.8,1.1.1.1
/ip firewall filter
add action=accept chain=forward comment="Allow established connections" \
    connection-state=established,related
add action=accept chain=forward comment="Allow authenticated hotspot users" \
    hotspot=auth
add action=drop chain=forward comment="Block unauthenticated hotspot users" \
    hotspot=!auth src-address=192.168.88.0/24
add action=accept chain=forward comment="Allow DNS" dst-port=53 protocol=udp
add action=accept chain=forward comment="Allow DNS TCP" dst-port=53 protocol=\
    tcp
add action=passthrough chain=unused-hs-chain comment=\
    "place hotspot rules here" disabled=yes
add action=accept chain=forward comment="Allow DNS" dst-port=53 protocol=udp
add action=accept chain=forward comment="Allow DHCP" dst-port=67-68 protocol=\
    udp
/ip firewall nat
add action=passthrough chain=unused-hs-chain comment=\
    "place hotspot rules here" disabled=yes
add action=masquerade chain=srcnat out-interface=ether1
/ip hotspot user
add name=admin
add name=monthly10k_user1 profile=Monthly-10K
add name=monthly15k_user1 profile=Monthly-15K
add name=daily_user1
/ip hotspot walled-garden
add comment="place hotspot rules here" disabled=yes
add dst-host=captive.apple.com
add dst-host=*.apple.com
/ip hotspot walled-garden ip
add action=accept disabled=no dst-host=*.mpesa.com
add action=accept disabled=no dst-host=*.paymentgateway.com
add action=accept disabled=no dst-host=*.google.com
add action=accept disabled=no dst-host=*.facebook.com
add action=accept comment="Mac captive portal" disabled=no dst-host=\
    captive.apple.com
add action=accept comment="Apple connectivity" disabled=no dst-host=\
    *.apple.com
add action=accept comment="Apple iCloud" disabled=no dst-host=*.icloud.com
add action=accept comment="Android detection" disabled=no dst-host=\
    connectivitycheck.gstatic.com
add action=accept comment="Google check" disabled=no dst-host=\
    clients3.google.com
add action=accept comment="Windows check" disabled=no dst-host=\
    www.msftconnecttest.com
/ip service
set www-ssl disabled=no
/system clock
set time-zone-name=Africa/Johannesburg
/system identity
set name=Hotspot-Router
/system note
set show-at-login=no
