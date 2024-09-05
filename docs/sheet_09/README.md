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

## Dovecot

Für die IMAP-Inbox benötigen wir (zusätzlich zu `dovecot-core`) noch `dovecot-imapd`, was wir mit `apt` installieren.
Die einzige Änderung, die wir an der Standard-Einstellung von Dovecot noch vornehmen müssen, ist, dass es Maildir verwendet.
Das geht über die `mail_location` in ``

Test, dass es funktioniert via telnet:

```
root@vmpsateam02-01:~# telnet 127.0.0.1 143
Trying 127.0.0.1...
Connected to 127.0.0.1.
Escape character is '^]'.
* OK [CAPABILITY IMAP4rev1 SASL-IR LOGIN-REFERRALS ID ENABLE IDLE LITERAL+ STARTTLS AUTH=PLAIN AUTH=LOGIN] Dovecot (Ubuntu) ready.
a login robyn.koelle <password> 
a OK [CAPABILITY IMAP4rev1 SASL-IR LOGIN-REFERRALS ID ENABLE IDLE SORT SORT=DISPLAY THREAD=REFERENCES THREAD=REFS THREAD=ORDEREDSUBJECT MULTIAPPEND URL-PARTIAL CATENATE UNSELECT CHILDREN NAMESPACE UIDPLUS LIST-EXTENDED I18NLEVEL=1 CONDSTORE QRESYNC ESEARCH ESORT SEARCHRES WITHIN CONTEXT=SEARCH LIST-STATUS BINARY MOVE SNIPPET=FUZZY PREVIEW=FUZZY PREVIEW STATUS=SIZE SAVEDATE LITERAL+ NOTIFY SPECIAL-USE] Logged in
a select INBOX
* FLAGS (\Answered \Flagged \Deleted \Seen \Draft)
* OK [PERMANENTFLAGS (\Answered \Flagged \Deleted \Seen \Draft \*)] Flags permitted.
* 8 EXISTS
* 8 RECENT
* OK [UNSEEN 1] First unseen.
* OK [UIDVALIDITY 1725572455] UIDs valid
* OK [UIDNEXT 9] Predicted next UID
a OK [READ-WRITE] Select completed (0.034 + 0.000 + 0.033 secs).
a fetch 1:* (FLAGS BODY[HEADER.FIELDS (FROM TO SUBJECT DATE)])
* 1 FETCH (FLAGS (\Seen \Recent) BODY[HEADER.FIELDS (FROM TO SUBJECT DATE)] {209}
Subject: This is just a test with nullmailer
To: <robyn.koelle@psa-team02.cit.tum.de>
Date: Thu,  5 Sep 2024 21:22:06 +0000
From: Testsystem check <root@vmpsateam02-02.vmpsateam02.psa-team02.cit.tum.de>
```

Für POP3 installieren wir analog `dovecot-pop3d`.
Test, dass es funktioniert via telnet:

```
root@vmpsateam02-01:~# telnet localhost 110
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
+OK Dovecot (Ubuntu) ready.
user robyn.koelle
+OK
pass <password> 
+OK Logged in.
list
+OK 8 messages:
1 801
2 801
3 801
4 786
5 782
6 878
7 732
8 735
.
retr 1
+OK 801 octets
Return-Path: <root@vmpsateam02-02.vmpsateam02.psa-team02.cit.tum.de>
X-Original-To: robyn.koelle@psa-team02.cit.tum.de
Delivered-To: robyn.koelle@psa-team02.cit.tum.de
Received: from vmpsateam02-02 (late-worm.psa-team02.cit.tum.de [192.168.2.2])
	by psa-team02.cit.tum.de (Postfix) with ESMTPA id 5493CA5A7C
	for <robyn.koelle@psa-team02.cit.tum.de>; Thu,  5 Sep 2024 19:23:47 +0000 (UTC)
Received: (nullmailer pid 17758 invoked by uid 0);
	Thu, 05 Sep 2024 21:22:06 -0000
Subject: This is just a test with nullmailer
To: <robyn.koelle@psa-team02.cit.tum.de>
User-Agent: mail (GNU Mailutils 3.16)
Date: Thu,  5 Sep 2024 21:22:06 +0000
Message-Id: <1725571326.880473.17757.nullmailer@vmpsateam02-02>
From: Testsystem check <root@vmpsateam02-02.vmpsateam02.psa-team02.cit.tum.de>
```

Dovecot stellt wie gefordert für jeden Nutzer unserer Team-VMs eine Mailbox bereit.
Diese können lokal auf `vmpsateam02-01` abgerufen werden.

