#!/bin/python3

import requests
from requests.auth import HTTPBasicAuth
import subprocess

# URL und Zugangsdaten für Nagios
nagios_url = "http://131.159.74.56:60205/nagios/"
nagios_username = "nagiosadmin"
nagios_password = "8a9MnsYX7pPr3BYX"

def check_nagios_web():
    """Prüft, ob die Nagios-Weboberfläche erreichbar ist."""
    try:
        # HTTP GET-Request mit Basic Auth
        response = requests.get(nagios_url, auth=HTTPBasicAuth(nagios_username, nagios_password))
        
        # Statuscode prüfen
        if response.status_code == 200:
            print("Nagios-Weboberfläche ist erreichbar und funktioniert einwandfrei.")
        elif response.status_code == 401:
            print("Zugriff verweigert. Falsche Anmeldeinformationen.")
        else:
            print(f"Nagios-Weboberfläche antwortet, aber mit einem Fehler. Statuscode: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Verbinden mit der Nagios-Weboberfläche: {e}")

def check_nagios_service():
    """Prüft lokal, ob der Nagios-Service läuft."""
    try:
        # Nagios-Service Status prüfen
        result = subprocess.run(['systemctl', 'is-active', 'nagios'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        service_status = result.stdout.decode().strip()

        if service_status == "active":
            print("Nagios-Service läuft.")
        else:
            print(f"Nagios-Service läuft nicht. Status: {service_status}")
    
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Überprüfen des Nagios-Service: {e}")

# Skript ausführen
if __name__ == "__main__":
    print("Prüfung des Nagios-Services...")
    check_nagios_service()

    print("\nPrüfung der Nagios-Weboberfläche...")
    check_nagios_web()
    
    
