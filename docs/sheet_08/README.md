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
Dabei geben wir die Admin-Credentials für unser LDAP Directory an (damit die ACLs in dem nachfolgenden Abschnitt uns keine Probleme bereiten).
Dabei ist es wichtig, dass die Reihenfolge der Authentifizierungsmethoden in `/etc/nsswitch.conf` mit `sss` beginnen, da LDAP als primäre Methode genutzt werden soll:

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


## ACL für Zugriffsbeschränkung bei anonymous bind

Der LDAP-Server war so konfiguriert, dass anonyme Benutzer (ohne Authentifizierung) uneingeschränkten Lesezugriff auf alle Einträge hatten.
Dies wurde durch die Standard-Access Control List (ACL) ermöglicht:
```
olcAccess: {2}to * by * read
```

Diese Regel erlaubt es jedem Benutzer, alle Daten zu lesen, was nicht den Sicherheitsanforderungen entspricht.
Wir wollen den Zugriff für anonyme Benutzer einschränken, sodass sie nur noch nach dem Attribut uid suchen können.
Wir haben die ACL auf dem LDAP-Server basierend auf den Erkenntnissen von Team10 angepasst.
Dabei wurde die Access Control List so modifiziert, dass anonyme Benutzer nur noch das uid-Attribut und den dazugehörigen Eintrag (entry) lesen können.

Erstellung der LDIF-Datei zur Modifikation der ACL (danke an Team10):
```
dn: olcDatabase={1}mdb,cn=config
changetype: modify
delete: olcAccess
olcAccess: {2}
-
add: olcAccess
olcAccess: {2} to attrs=uid by * read
olcAccess: {3} to attrs=entry by * read
olcAccess: {4} to * by self write by users read by * none
```

- `olcAccess: {2} to attrs=uid by * read`: Erlaubt allen Benutzern, einschließlich anonymer Benutzer, das Lesen des uid-Attributs.
- `olcAccess: {3} to attrs=entry by * read`: Erlaubt das Lesen des Eintrags selbst, was notwendig ist, um auf das uid-Attribut zuzugreifen.
- `olcAccess: {4} to * by self write by users read by * none`: Erlaubt authentifizierten Benutzern das Ändern ihrer eigenen Einträge und das Lesen anderer Einträge. Anonyme Benutzer erhalten hier keine weiteren Rechte.

Die Änderungen haben wir mittels `ldapmodify` angewendet.

Nach der Anpassung der ACL können anonyme Benutzer nur noch das uid-Attribut und den dazugehörigen Eintrag lesen.
Alle anderen Zugriffe für anonyme Benutzer wurden deaktiviert.
Authentifizierte Benutzer behalten die Möglichkeit, ihre eigenen Einträge zu ändern und die Einträge anderer Benutzer zu lesen.

Eine Testsuche bestätigte, dass die ACL-Regeln wie erwartet funktionieren.

## CSV-User anlegen

Wir schreiben ein Python-Skript, um uns Ansible-Variablen für die User der CSV zu erzeugen.
Dafür haben wir einen `dev-scripts`-Ordner in der Rolle [ldap-csv-users](../roles/ldap-csv-users) angelegt.
Das Skript generiert außerdem die X.509 Zertifikate, und schreibt sie in Dateien.
Diese hinterlegen wir im `templates`-Ordner der Rolle.
Die Keys verschlüsseln wir mit `ansible-vault`.
Wir kopieren die Zertifikate (nur auf `vmpsateam02-01` - da aktuell nicht auf der anderen VM notwendig) nach `/usr/local/share/ldap-csv-user-certificates`). 
Die LDAP-User legen wir mittels einer LDIF und dem `inetOrgPerson` an, das unter anderem das `userCertificate`-Feld unterstützt.
Notiz: obwohl in der Aufgabenstellung steht, dass wir den public-Key des Zertifikats hinterlegen sollen, hinterlegen wir das User-Zertifikat, da dieses direkt von LDAP unterstützt wird, und uns sinnvoller erscheint.
Den Public-Key könnte man aber leicht (z.B. im Python Skript) aus dem Zertifikat extrahieren, und in einem anderen Feld des LDAP-User-Entries speichern.
Dieses geben wir in Base64 im DER-Format an.
Wir nutzen `ldapadd` analog wie oben, um die User anzulegen.

