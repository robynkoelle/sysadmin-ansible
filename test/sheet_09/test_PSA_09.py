#!/bin/python3

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import random
import os
import string
import subprocess
import socket

# SMTP-Server-Konfiguration
smtp_server = "psa-team02.cit.tum.de"
smtp_port = 25  
smtp_user = "robyn.koelle"
smtp_password = "MkfFtaTzw7"

# E-Mail-Konfiguration
absender_email = "robyn.koelle@psa-team02.cit.tum.de"
empfaenger_email = "root@psa-team02.cit.tum.de"
betreff = "Test-E-Mail"
random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
nachricht_text = "Random test string: " + random_string

# E-Mail erstellen
nachricht = MIMEMultipart()
nachricht['From'] = absender_email
nachricht['To'] = empfaenger_email
nachricht['Subject'] = betreff

# Nachrichtentext hinzufügen
nachricht.attach(MIMEText(nachricht_text, 'plain'))

# E-Mail senden
try:
    server = smtplib.SMTP(smtp_server, smtp_port)

    # Try login and check for success
    try:
        server.login(smtp_user, smtp_password)  # Authentifizierung mit Benutzername und Passwort
        print("Login successful!")
    except smtplib.SMTPAuthenticationError as e:
        print(f"Login failed: {e}")
        server.quit()
        exit(1)

    text = nachricht.as_string()
    response = server.sendmail(absender_email, empfaenger_email, text)
    server.quit()
    
    if not response:
        print("E-Mail erfolgreich gesendet und weitergeleitet!")
    else:
        print("E-Mail gesendet, aber es gab ein Problem mit der Weiterleitung:")
        print(response)

except Exception as e:
    print(f"Fehler beim Senden der E-Mail: {e}")

time.sleep(5)

maildir_path = "/root/Maildir/new"  # Pfad zu dem Maildir des Empfängers

try:
    found = False
    virus_scanned = False  # To track if X-Virus-Scanned is found
    for root, dirs, files in os.walk(maildir_path):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_contents = f.read()
                if random_string in file_contents:
                    print(f"Zufallsstring '{random_string}' in der Datei {file_path} gefunden!")
                    found = True
                    # Check for 'X-Virus-Scanned' header
                    if 'X-Virus-Scanned' in file_contents:
                        virus_scanned = True
                    break
        if found:
            break
    
    if not found:
        print(f"Zufallsstring '{random_string}' wurde nicht in der Maildir gefunden.")
    
    if virus_scanned:
        print("The email was virus-scanned ('X-Virus-Scanned' header found).")
    else:
        print("The 'X-Virus-Scanned' header was not found in the email.")
    
except Exception as e:
    print(f"Fehler beim Durchsuchen der Maildir: {e}")

# Additional functions to test Dovecot and Postfix

# Function to check if Dovecot service is running
def check_dovecot_running():
    print("Checking if Dovecot service is running...")
    try:
        result = subprocess.run(['systemctl', 'is-active', '--quiet', 'dovecot'])
        if result.returncode == 0:
            print("Dovecot is running.")
        else:
            print("Dovecot is NOT running!")
    except Exception as e:
        print(f"Error checking Dovecot status: {e}")

# Function to check if Dovecot is listening on the appropriate ports (IMAP and POP3)
def check_dovecot_ports():
    print("Checking if Dovecot is listening on IMAP and POP3 ports...")

    ports = {
        'IMAP': 143,
        'IMAPS': 993,
        'POP3': 110,
        'POP3S': 995
    }

    for service, port in ports.items():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                print(f"Dovecot is listening on {service} (port {port}).")
            else:
                print(f"Dovecot is NOT listening on {service} (port {port}).")


# Function to test Dovecot authentication via IMAP
def test_dovecot_authentication():
    print("Testing Dovecot authentication for user 'adrian.averwald'...")

    # Use a test user to check IMAP authentication (replace with actual credentials)
    user = "adrian.averwald"
    password = "MkfFtaTzw7"

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(('localhost', 143))
            data = sock.recv(1024)
            to_send = b'a login ' + user.encode() + b' ' + password.encode() + b'\n'
            sock.sendall(to_send)
            data = sock.recv(1024)
            if b"a OK" in data:
                print(f"IMAP authentication for {user} was successful.")
            else:
                print(f"IMAP authentication for {user} failed.")
            sock.sendall(b"a select INBOX\n")
            data = sock.recv(1024)
            if b"a OK" in data:
                print(f"INBOX selected successfully.")
    except Exception as e:
        print(f"Error during IMAP authentication: {e}")



# Run Dovecot and Postfix tests after sending email
check_dovecot_running()
check_dovecot_ports()
test_dovecot_authentication()

print("Dovecot and Postfix tests completed.")
