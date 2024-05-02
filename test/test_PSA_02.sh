#!/bin/bash

echo "Test der Netzwerkkonfigurationen"
echo "================================="

# Definition der Subnets
CONNECTION_SUBNETS=(1 2 3 4 5 6 7 8 9 10)

# Anzeige der Netzwerkadapter-Konfigurationen
echo "Anzeige der IP-Konfiguration für alle Netzwerk-Adapter:"
ip addr show

# Testen der Konnektivität innerhalb des eigenen Subnetzes
echo "Ping-Test innerhalb des eigenen Subnetzes:"
echo "================================="
nmap -sn 192.168.2.0/24


# Testen der Verbindung zwischen den Subnetzen
echo "Ping-Test zwischen den Subnetzen:"
echo "================================="
for idx in ${CONNECTION_SUBNETS[@]}; do
        other_team_subnet="192.168.${TEAM_NR}${idx}.0/24"
        echo "Nmap-Scan des Subnetzes $other_team_subnet ..."
	echo "-     ================================="
	nmap -sn 192.168.${idx}.0/24 --host-timeout 2ms --max-retries 1 -T5
done

echo "Test der Firewall-Konfigurationen"
echo "=================================="

# Testen der Zugänglichkeit der Ports 22, 80 und 443
echo "Testen der Ports für eingehende Verbindungen:"
echo "TODO"

# Überprüfung der Firewall-Regeln
echo "Anzeige der aktuellen Firewall-Regeln:"
iptables -L

# Überprüfung des korrekten Funktionierens der DNS-Auflösung
echo "DNS-Resolution-Test:"
nslookup google.com

echo "Test abgeschlossen"