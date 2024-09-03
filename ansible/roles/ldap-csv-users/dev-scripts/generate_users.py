#!/bin/python3
import base64
import csv
import yaml
from OpenSSL import crypto

csv_file_path = "benutzerdaten.csv"
yaml_file_path = "output.yaml"

users = []


# From https://stackoverflow.com/questions/27164354/create-a-self-signed-x509-certificate-in-python
def cert_gen(commonName="team02",
             validityStartInSeconds=0,
             validityEndInSeconds=10 * 365 * 24 * 60 * 60,
             KEY_FILE="private.key",
             CERT_FILE="selfsigned.crt"):
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 4096)

    # Create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().CN = commonName
    cert.gmtime_adj_notBefore(validityStartInSeconds)
    cert.gmtime_adj_notAfter(validityEndInSeconds)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha512')
    with open(CERT_FILE, "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
    with open(KEY_FILE, "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("utf-8"))

    return cert


with open('benutzerdaten.csv', mode='r', encoding='utf-8') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        cert = cert_gen(KEY_FILE=f"{row['Matrikelnummer']}.key", CERT_FILE=f"{row['Matrikelnummer']}.crt")

        # Encode DER format certificate to Base64
        cert_der = crypto.dump_certificate(crypto.FILETYPE_ASN1, cert)
        cert_base64 = base64.b64encode(cert_der).decode("utf-8")

        user = {
            'name': row['Name'],
            'first_name': row['Vorname'],
            'gender': row['Geschlecht'],
            'birthdate': row['Geburtsdatum'],
            'birthplace': row['Geburtsort'],
            'nationality': row['Nationalität'],
            'street': row['Straße'],
            'postal_code': row['PLZ'],
            'city': row['Ort'],
            'phone': row['Telefon'],
            'matriculation_number': row['Matrikelnummer'],
            'user_cert': cert_base64,
        }
        users.append(user)

data = {"ldap_csv_users": users}

with open(yaml_file_path, mode="w", encoding="utf-8") as yaml_file:
    yaml.dump(data, yaml_file, default_flow_style=False, allow_unicode=True)

