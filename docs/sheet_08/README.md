# Aufgabenblatt 8: LDAP

## LDAP installieren
Wir installieren `slapd` und `ldap-utils` mit apt:
```shell
apt install slapd ldap-utils
```
Bei dem Prompt wird das Admin Passwort gesetzt.

## LDAP konfigurieren
Bei dieser Aufgabe haben wir uns dazu entschieden einen Teil der Konfiguration interaktiv im Terminal zu machen, anstatt wie bei den anderen Aufgaben mit Ansible: `dpkg-reconfigure slapd`

- Omit OpenLDAP server configuraiotn: No
- DNS domain name: team02.psa.cit.tum.de
    - Notiz: diese Domain geben wir an, um den geforderten DIT-Prefix `dc=team02,dc=psa,dc=cit,dc=tum,dc=de` zu bekommen. Wir legen dennoch einen DNS Eintrag für `ldap.psa-team02.cit.tum.de` bei unserem DNS Server an (was auch das Zertifikat betrifft, das weiter unten in diesem Dokument beschrieben ist).
- Organization name: team02
- Administrator password of the LDAP directory: `bobby_tables`
- Database remove when slapd is purged: No

Um die Konfiguration von `slapd` zu erleichtern, legen wir in der Datei `ldap.conf` folgende Variablen an:
```
TLS_CACERT	/etc/ssl/certs/ca-certificates.crt

BASE dc=team02,dc=psa,dc=cit,dc=tum,dc=de
URI ldap://ldap.psa-team02.cit.tum.de
```



## SSL: TLS für LDAP einrichten

Für die verschlüsselte Kommunikation zwischen Client und Server generieren wir ein selbst signiertes Zertifikat. Diese Schritte stellen sicher, dass die LDAP-Kommunikation mittels TLS gesichert wird.

### CA-Schlüssel und -Zertifikat erstellen
Zuerst erstellen wir einen privaten Schlüssel für unsere eigene Certificate Authority (CA):

```shell
sudo certtool --generate-privkey --bits 4096 --outfile /etc/ssl/private/cakey.pem
```

Dann erstellen wir eine Konfigurationsdatei `ca.info`, die die Informationen für unser CA-Zertifikat enthält:

```
cn = team02
ca
cert_signing_key
expiration_days = 3650
```

Nun erzeugen wir das selbst signierte CA-Zertifikat:

```shell
sudo certtool --generate-self-signed \
--load-privkey /etc/ssl/private/cakey.pem \
--template ca.info \
--outfile /usr/local/share/ca-certificates/cacert.crt
```

Um das neue CA-Zertifikat in die Liste der vertrauenswürdigen Zertifikate aufzunehmen, führen wir den folgenden Befehl aus:

```shell
sudo update-ca-certificates
```

### Server-Schlüssel und -Zertifikat erstellen
Mit dem CA-Zertifikat können wir nun das Schlüsselpaar für unser LDAP erstellen. Dies erfolgt ähnlich wie bei der Erstellung des CA-Zertifikats:

1. **Erstellen des privaten Schlüssels für den LDAP-Server:**
   ```shell
   sudo certtool --generate-privkey --bits 2048 --outfile /etc/ldap/ldap01_slapd_key.pem
   ```

2. **Erstellen der Konfigurationsdatei `ldap01.info`:**
   ```
   organization = team02
   cn = ldap.psa-team02.cit.tum.de
   tls_www_server
   encryption_key
   signing_key
   expiration_days = 365
   ```

3. **Erstellen des Server-Zertifikats:**
   ```shell
   sudo certtool --generate-certificate \
   --load-privkey /etc/ldap/ldap01_slapd_key.pem \
   --load-ca-certificate /etc/ssl/certs/cacert.pem \
   --load-ca-privkey /etc/ssl/private/cakey.pem \
   --template ldap01.info \
   --outfile /etc/ldap/ldap01_slapd_cert.pem
   ```

### Berechtigungen und Eigentümerschaft anpassen
Um sicherzustellen, dass nur der `openldap`-Benutzer Zugriff auf den Schlüssel hat, passen wir die Berechtigungen wie folgt an:

```shell
sudo chgrp openldap /etc/ldap/ldap01_slapd_key.pem
sudo chmod 0640 /etc/ldap/ldap01_slapd_key.pem
```

### LDAP mit TLS konfigurieren
Nun erstellen wir die Datei `certinfo.ldif`, die die TLS-Konfigurationsinformationen enthält:

```ldif
dn: cn=config
add: olcTLSCACertificateFile
olcTLSCACertificateFile: /etc/ssl/certs/cacert.pem
-
add: olcTLSCertificateFile
olcTLSCertificateFile: /etc/ldap/ldap01_slapd_cert.pem
-
add: olcTLSCertificateKeyFile
olcTLSCertificateKeyFile: /etc/ldap/ldap01_slapd_key.pem
```

Diese Konfigurationsdatei wird dann mit dem `ldapmodify`-Befehl angewendet:

```shell
sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f certinfo.ldif
```

Falls du auch LDAPS (LDAP über SSL) aktivieren möchtest, musst du `/etc/default/slapd` bearbeiten und `ldaps:///` zu `SLAPD_SERVICES` hinzufügen:

```shell
SLAPD_SERVICES="ldap:/// ldapi:/// ldaps:///"
```

Anschließend muss der `slapd`-Dienst neu gestartet werden:

```shell
sudo systemctl restart slapd
```

### TLS und LDAPS testen

Um sicherzustellen, dass die TLS-Verbindung funktioniert, können folgende Tests durchgeführt werden:

1. **StartTLS testen:**
   ```shell
   ldapwhoami -x -ZZ -H ldap://ldap.psa-team02.cit.tum.de
   ```

2. **LDAPS testen:**
   ```shell
   ldapwhoami -x -H ldaps://ldap.psa-team02.cit.tum.de
   ```


## User und Gruppen anlegen

Wir nutzen `ldapadd` und Ansible-Templating, um unsere Gruppen und Nutzer anzulegen.
Unsere Ansible-Variablen fungieren als Source-of-Truth für die UIDs und GIDs, die wir an LDAP weitergeben.
Die LDIF-Dateien sind in [roles/ldap/templates](../roles/ldap/templates).

## LDAP als Client nutzen

Wir installieren auf allen LDAP-clients SSSD und ldap-utils.
Wir konfigurieren SSSD wie in [sssd.conf](../roles/ldap-client/templates/etc/sssd/sssd.conf) beschrieben.
Dabei ist es wichtig, dass die Reihenfolge der Authentifizierungsmethoden mit `sss` beginnt, da LDAP als primäre Methode genutzt werden soll.
`passwd: sss files systemd`
Diese Einstellung stellt genau das sicher.

Auf den Clients müssen wir zusätzlich noch dem selbst erzeugten CA-Zertifikat (siehe oben) vertrauen.
Dies machen wir mit `update-ca-certificates`, nachdem wir es unter `/usr/local/share/ca-certificates/` abgelegt haben.

Zusätzlich geben wir in `iptables` noch die LDAP-Ports frei.

Wir verifizieren wie folgt, dass der LDAP(S) Zugriff funktioniert:
```
root@vmpsateam02-02:~# ldapwhoami -x -ZZ -H ldap://ldap.psa-team02.cit.tum.de
anonymous
root@vmpsateam02-02:~# ldapwhoami -x -H ldaps://ldap.psa-team02.cit.tum.de
anonymous
```

Die Funktionalität wurde mit passwd getestet, indem ein neues Passwort gesetzt wurde und der veränderte hash mit ldapsearch überprüft wurde.

