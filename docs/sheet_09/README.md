# Aufgabenblatt 09: Dokumentation

## Postfix

Wir halten uns grob an die Ubuntu-Dokumentation / Tutorial für Postfix:
https://documentation.ubuntu.com/server/how-to/mail-services/install-postfix/

Wir installieren `postfix` über `apt`.
Wir konfigurieren `postfix` wie in der [mail-Rolle](../../ansible/roles/mail) beschrieben.
Wir editieren die (mitgelieferte) `/etc/postfix/main.cf`, und heben folgende Konfigurationen für die Dokumentation hervor:

Vermeiden dass wir ein open relay sind durch folgende Zeile in der `/etc/postfix/main.cf`:
```
smtpd_recipient_restrictions = permit_sasl_authenticated,permit_mynetworks,reject_unauth_destination
```

Angegebene Domain bei ausgehenden E-Mails:
```
myhostname = psa-team02.cit.tum.de
```

Mails mit dieser destination werden angenommen:
```
mydestination = psa-team02.cit.tum.de, vmpsateam02-01.psa-team02.cit.tum.de, vmpsateam02-01, localhost.localdomain, , localhost
```

Gegebenen Mail-Relay konfigurieren:
```
relayhost = mailrelay.cit.tum.de
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
smtpd_sasl_type = dovecot
smtpd_sasl_path = private/auth
smtpd_sasl_local_domain =
smtpd_sasl_security_options = noanonymous
smtpd_sasl_tls_security_options = noanonymous
broken_sasl_auth_clients = yes
smtpd_sasl_auth_enable = yes
```

Für die SMTP-Authentication benötigen wir mindestens `dovecot-core` (mit `apt` installiert), und die folgende Konfiguration.

### Dovecot für SASL

Für die Authentifizierung / SASL:
```
# /etc/dovecot/conf.d/10-master.conf

service auth {
  # auth_socket_path points to this userdb socket by default. It's typically
  # used by dovecot-lda, doveadm, possibly imap process, etc. Its default
  # permissions make it readable only by root, but you may need to relax these
  # permissions. Users that have access to this socket are able to get a list
  # of all usernames and get results of everyone's userdb lookups.
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

