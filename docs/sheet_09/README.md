# Aufgabenblatt 09: Dokumentation

## Postfix

Wir halten uns grob an die Ubuntu-Dokumentation / Tutorial für Postfix:
https://documentation.ubuntu.com/server/how-to/mail-services/install-postfix/

Wir installieren `postfix` über `apt`.
Wir konfigurieren `postfix` wie in der [mail-Rolle](../../ansible/roles/mail) beschrieben.
Wir editieren die (mitgelieferte) `/etc/postfix/main.cf`, und heben folgende Konfigurationen für die Dokumentation hervor:

Vermeiden, dass wir ein open relay sind durch folgende Zeilen in der `/etc/postfix/main.cf`:
```
smtpd_relay_restrictions = permit_sasl_authenticated, permit_mynetworks, reject
```

Mails für unbekannte Empfänger bereits im SMTP-Dialog ablehnen:
```
# Restrict email acceptance 
smtpd_recipient_restrictions = 
    reject_unlisted_recipient,
    permit_sasl_authenticated,
    permit_mynetworks,
    reject
```

Mails nur von bekannten Nutzern annehmen:
```
smtpd_sender_restrictions = permit_sasl_authenticated, reject
```

Angegebene Domain bei ausgehenden E-Mails:
```
myhostname = psa-team02.cit.tum.de
```

Mails mit dieser destination werden angenommen:
```
mydestination = psa-team02.cit.tum.de, vmpsateam02-01.psa-team02.cit.tum.de, vmpsateam02-01, localhost.localdomain, , localhost
```

Gegebenen Mail-Relay konfigurieren (für Mails, die an User gehen, die wir nicht verwalten):
```
relayhost = mailrelay.cit.tum.de
```

Umschreiben der Senderadresse bei Relay:
```
## Header rewriting:
smtpproxy_generic_sender = noreply@tum.de
```

Beschränkung für Netzwerke, die uns anfragen können:
```
mynetworks = 192.168.2.0/24 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128
```

`Maildir` einrichten:
```
home_mailbox = Maildir/
```

SMTP-Authentication einrichten:
```
# Dovecot SASL:
smtpd_sasl_type = dovecot
smtpd_sasl_path = private/auth
smtpd_sasl_local_domain = $myhostname
smtpd_sasl_security_options = noanonymous
broken_sasl_auth_clients = yes
smtpd_sasl_auth_enable = yes
```

Für die SMTP-Authentication benötigen wir mindestens `dovecot-core` (mit `apt` installiert), und die folgende Konfiguration.

### Dovecot für SASL

Für die Authentifizierung / SASL:
```
# /etc/dovecot/conf.d/10-master.conf

service auth {
  unix_listener auth-userdb {
    #mode = 0600
    #user = 
    #group = 
  }
    
  # Postfix smtp-auth
  unix_listener /var/spool/postfix/private/auth {
    mode = 0660
    user = postfix
    group = postfix
  }
 }
```

Und in `/etc/dovecot/conf.d/10-auth.conf`: `auth_mechanisms = plain login`

Per default verwendet dovecot jeweils pam und passwd als Driver für passdb bzw. userdb.
Demnach entspricht die SASL-Authentifizierung bei Postfix insgesamt der folgenden Kette:
Postfix -> Dovecot SASL -> PAM -> SSSD -> LDAP.
Man authentifiziert sich also mit seinen LDAP-Credentials.

## Testen

Mit `telnet psa-team02.cit.tum.de 25` und anschließendem `ehlo psa-team02.cit.tum.de` können wir anhand der Antwort verifizieren, dass Postfix grundlegend läuft:

```
root@vmpsateam02-01:~# telnet psa-team02.cit.tum.de 25
Trying 192.168.2.1...
Connected to psa-team02.cit.tum.de.
Escape character is '^]'.
220 psa-team02.cit.tum.de ESMTP Postfix (Ubuntu)
ehlo psa-team02.cit.tum.de
250-psa-team02.cit.tum.de
250-PIPELINING
250-SIZE 10240000
250-VRFY
250-ETRN
250-STARTTLS
250-AUTH PLAIN LOGIN
250-AUTH=PLAIN LOGIN
250-ENHANCEDSTATUSCODES
250-8BITMIME
250-DSN
250-SMTPUTF8
250 CHUNKING
quit
221 2.0.0 Bye
Connection closed by foreign host.
```

## Ersetzen von Subdomains

Wenn die Sender-Adresse einer Mail (FROM) die Struktur jemand@subdomain.psa-team02.cit.tum.de hat, können wir die Subdomain aus der Absenderadresse entfernen, indem wir eine `/etc/header_checks`-Datei anlegen, und diese in Postfix' `main.cf` als `header_checks` angeben:

```
header_checks = regexp:/etc/postfix/header_checks
```

Die Datei nutzt eine Regex, um die Subdomain aus der ursprünglichen Adresse zu entfernen:
```
/^From:\s*([^@]+)@subdomain\.(psa-team[0-9]{2}\.cit\.tum\.de)/ REPLACE From: ${1}@${2}
```

Dass es funktioniert sehen wir dann nach Senden einer Beispiel-Mail im `/var/log/mail.log`:

```
2024-09-04T22:15:43.011832+00:00 vmpsateam02-01 postfix/cleanup[23022]: 01E2BA5AAD: replace: header From: robyn.koelle@subdomain.psa-team02.cit.tum.de from early-bird.psa-team02.cit.tum.de[192.168.2.1]; from=<robyn.koelle@subdomain.psa-team02.cit.tum.de> to=<adrian.averwald@psa-team02.cit.tum.de> proto=ESMTP helo=<[10.0.2.15]>: From: robyn.koelle@psa-team02.cit.tum.de
```

## Postmaster

Die Datei `/etc/aliases` definiert root als unseren `postmaster`.
Hier könnte man eine Admin-Adresse hinterlegen - für unseren Use Case ist aber der `root`-User gut geeignet und eine pragmatische Lösung.
Man kann die korrekte Funktion testen, indem man eine E-Mail an `postmaster@psa-team02.cit.tum.de` adressiert.
Die Mail taucht dann unter `/root/Maildir/new` auf.

## MX Records

Die MX Records haben wir in unserer `bin9`-config angelegt:
```
$TTL 1d
$ORIGIN psa-team02.cit.tum.de.

@               IN      SOA   ns1.psa-team02.cit.tum.de. admin.psa-team02.cit.tum.de. (
                                6       ; Serial
                                1w      ; Refresh
                                15m     ; Retry
                                3w      ; Expire
                                2h      ; Negative Cache TTL
                              )

                IN      NS      ns1.psa-team02.cit.tum.de.
                IN      NS      ns.psa-team09.cit.tum.de.
                IN      MX      10 mail.psa-team02.cit.tum.de.
                IN      A       192.168.2.1
mail            IN      A       192.168.2.1
ns1             IN      A       192.168.2.1

www             IN      CNAME   early-bird
early-bird      IN      A       192.168.2.1
early-bird      IN      MX      10 mail.psa-team02.cit.tum.de.

late-worm       IN      A       192.168.2.2
late-worm       IN      MX      10 mail.psa-team02.cit.tum.de.

bearly-ird      IN      A       192.168.2.3
bearly-ird      IN      MX      10 mail.psa-team02.cit.tum.de.

db              IN      A       192.168.2.1
db              IN      MX      10 mail.psa-team02.cit.tum.de.

ldap            IN      A       192.168.2.1
ldap            IN      MX      10 mail.psa-team02.cit.tum.de.
```

## Mails der VMs

Wir installieren auf `vmpsateam02-02` (unsere einzige andere VM) einen lightweight, relay-only MTA namens `nullmailer` via `apt`.
Dies erfordert nur 3 Konfigurationsdateien in `/etc/nullmailer` (Zitat aus der [Doku](https://wiki.debian.org/nullmailer)):
- adminaddr - contains the target email address to send emails
- defaultdomain - marks the domain the emails are sent from
- remotes - contains the email login configuration on the remote system

Die konkreten Werte können in der `nullmailer`-Rolle eingesehen werden.
Wir haben uns einen `mailuser` auf `vmpsateam02-01` angelegt, über den wir uns authentifizieren.

Testen, dass es funktioniert:
```
root@vmpsateam02-02:~# echo "hi RK" |mail -s "RK Test" "robyn.koelle@psa-team02.cit.tum.de"
root@vmpsateam02-02:~# cat /home/robyn.koelle/Maildir/new/* |grep RK
Subject: RK Test
Subject: RK Test
hi RK
```
Notiz: da das `home`-Verzeichnis automounted und somit mit `vmpsateam02-01` synchron ist, können wir direkt auf `vmpsateam02-01` in das Maildir des Empfängers schauen.
Notiz: das hier verwendete `mail` CLI-Tool ist in dem Paket `mailutils` enthalten.

