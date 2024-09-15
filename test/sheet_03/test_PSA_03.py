#!/bin/python3

import subprocess
import re

def fuehre_nmap_aus():
    print("Führe nmap DHCP-Entdeckung aus...")
    command = ["nmap", "--script", "broadcast-dhcp-discover", "-e", "enp0s8"]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout

def pruefe_antwort(response, key, erwarteter_wert):
    lines = response.splitlines()
    for line in lines:
        if key in line:
            index = line.find(key)
            if line[index + len(key):].strip().startswith(':'):
                actual_value = line[index + len(key) + 1:].strip()
                if actual_value == erwarteter_wert:
                    print(f"OK: {key} ist {erwarteter_wert}")
                    return
                else:
                    print(f"FEHLER: {key} ist {actual_value}, erwartet wurde {erwarteter_wert}")
                    return 
    print(f"FEHLER: {key} wurde nicht in der Antwort gefunden")

def test_dhcp_entdeckung():
    output = fuehre_nmap_aus()
    splits = output.split("Response")

    for part in splits:
        if "192.168.2.1" in part:
            print(f"ANTWORT:\n{part}")
            pruefe_antwort(part, "WPAD", "http://pac.lrz.de")

def test_dns_aufloesung(domain_name, erwartete_ip):
    print(f"Teste DNS-Auflösung für {domain_name}...")
    try:
        result = subprocess.run(['dig', '+short', domain_name], capture_output=True, text=True)
        resolved_ip = result.stdout.strip()
        if resolved_ip == erwartete_ip:
            print(f"Erfolg: {domain_name} löst auf {resolved_ip}")
        else:
            print(f"FEHLER: {domain_name} löst auf {resolved_ip}, erwartet wurde {erwartete_ip}")
    except Exception as e:
        print(f"Fehler bei der DNS-Auflösung: {e}")

def test_reverse_dns(ip_adresse, erwartete_domain):
    print(f"Teste Reverse DNS-Auflösung für {ip_adresse}...")
    try:
        result = subprocess.run(['dig', '-x', ip_adresse, '+short'], capture_output=True, text=True)
        resolved_domain = result.stdout.strip()
        if erwartete_domain in resolved_domain.splitlines():
            print(f"Erfolg: {ip_adresse} wird auf {resolved_domain} aufgelöst")
        else:
            print(f"FEHLER: {ip_adresse} wird auf {resolved_domain} aufgelöst, erwartet wurde {erwartete_domain}")
    except Exception as e:
        print(f"Fehler bei der Reverse DNS-Auflösung: {e}")

def test_dhcp_leasing(schnittstelle):
    print(f"Teste DHCP-Leasing auf {schnittstelle}...")
    try:
        result = subprocess.run(['dhclient', '-v', schnittstelle], capture_output=True, text=True)
        if "bound to" in result.stdout:
            print(f"Erfolg: DHCP-Lease auf {schnittstelle} erhalten")
        else:
            print(f"FEHLER: Kein DHCP-Lease auf {schnittstelle} erhalten")
    except Exception as e:
        print(f"Fehler beim Testen des DHCP-Leasings: {e}")

def test_dns_weiterleitung(domain_name):
    print(f"Teste DNS-Weiterleitung für {domain_name}...")
    try:
        result = subprocess.run(['dig', '+short', domain_name], capture_output=True, text=True)
        if result.stdout.strip():
            print(f"Erfolg: DNS-Weiterleitung funktioniert für {domain_name}")
        else:
            print(f"FEHLER: DNS-Weiterleitung funktioniert nicht für {domain_name}")
    except Exception as e:
        print(f"Fehler bei der DNS-Weiterleitung: {e}")

def main():
    test_dns_aufloesung("psa-team02.cit.tum.de", "192.168.2.1")
    test_reverse_dns("192.168.2.2", "vmpsateam02-02.psa-team02.cit.tum.de.")
    test_dns_weiterleitung("www.google.com")
    test_dhcp_entdeckung()

if __name__ == "__main__":
    main()
