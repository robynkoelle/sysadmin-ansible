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

