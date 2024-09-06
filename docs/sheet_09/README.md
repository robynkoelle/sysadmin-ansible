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

### Mail-Weiterleitung

Für die Mail-Weiterleitung orientieren wir uns größtenteils an der Lösung von Team09 (danke).

Wir setzen den `relayhost` auf einen leeren Wert, weil wir transport maps verwenden wollen:
```
relayhost =
transport_maps = hash:/etc/postfix/transport
```

In der transport map geben wir je Domain an, über welchen Server die Mail geschickt werden soll.
Hier geben wir unseren eigenen Mail-Server für die von uns verwalteten Domains an,
sowie analog die der anderen Teams.
Alle restlichen Emails schicken wir über `mailrelay.cit.tum.de`.
Die Datei `/etc/postfix/transport` kann man in der [mail-Rolle](../../ansible/roles/mail) unter `templates` einsehen.
Diese müssen wir noch mit `postmap /etc/postfix/transport` mappen, damit eine `transport.db`-Datei entsteht.

Um die Sender-Adresse beim Relay umzuschreiben, erstellen wir einen Service in der `/etc/postfix/master.cf`:
```
smtp_extern      unix  -       -       n       -       -       smtp
  -o smtp_generic_maps=hash:/etc/postfix/generic
  -o relayhost=mailrelay.cit.tum.de
```

Die referenzierte Datei `/etc/postfix/generic` kann man ebenfalls in den Rollen-Templates einsehen.
Diese mappen wir ebenso mit `postmap`.

Nach einem Neustart des `postfix` Services können wir die Funktionalität testen:
```
echo "Testnachricht" |mail -s "Testbetreff" -r "robyn.koelle@psa-team02.cit.tum.de" robyn.koelle@tum.de
```

Der Mail-Log (und ein Blick ins Postfach) bestätigt, dass die Mail über den Relay geschickt wurde:
```
2024-09-06T23:43:22.352075+00:00 vmpsateam02-01 postfix/smtp[55862]: 4DC1BA5B39: to=<robyn.koelle@tum.de>, relay=mailrelay.in.tum.de[131.159.254.10]:25, delay=0.03, delays=0.01/0/0.01/0.02, dsn=2.0.0, status=sent (250 2.0.0 Ok: queued as 549DA1D9)
```

Der Mail-Log bestätigt analog, dass Mails an die jeweiligen Mailserver der anderen Teams übertragen wurden, zum Beispiel bei einer Nachricht an `lukas.eckert@psa-team09.cit.tum.de`. 

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

## Virenscanner und Spam-Filter

Wir erhöhen zunächst den Arbeitsspeicher von `vmpsateam02-01` auf 4096MB über die Virtualbox GUI.
Wir halten uns in diesem Abschnitt an [dieses Tutorial](https://help.ubuntu.com/community/PostfixAmavisNew).

Wir installieren mit `apt` die Pakete `amavisd-new`, `spamassassin`, und `clamav-daemon`.
Damit Clamav Zugriff zu den notwendigen Dateien hat, fügen wir den `clamav`-User der `amavis`-Gruppe hinzu, und umgekehrt.
Der `clamav-freshclam`-Service hält die Virusdefinitionen aktuell.
Damit der Download über unsere Proxy geht, müssen wir `HTTPProxyServer proxy.cit.tum.de` in `/etc/clamav/freshclam.conf` setzen (und den Service neustarten).
Ansonsten sind die Standard-Einstellungen von Clamav für uns ausreichend.

Amavis stellt einen eigenständigen daemon zur Verfügung, der die Spamassassin-Libraries verwendet - daher müssen wir Spamassassin selbst nicht weiter konfigurieren.
Wir aktivieren die Spam- und Antivirus-Funktion von Amavis mittels der Datei `/etc/amavis/conf.d/15-content_filter_mode`.
Zusätzlich spezifizieren wir die "lokalen" Domains, die Postfix verwaltet, für Amavis in `/etc/amavis/conf.d/05-domain_id`.
In `/etc/amavis/conf.d/50-user` whitelisten wir diese Domains.
Die Config-Dateien können in der [mail-Rolle](../../ansible/roles/mail) unter `templates` eingesehen werden.

Wir teilen Postfix den Content-Filter in der `main.cf` mit:
```
content_filter = smtp-amavis:[127.0.0.1]:10024
```

Zusätzlich fügen wir folgenden Abschnitt der `master.cf` hinzu:
```
smtp-amavis     unix    -       -       -       -       2       smtp
        -o smtp_data_done_timeout=1200
        -o smtp_send_xforward_command=yes
        -o disable_dns_lookups=yes
        -o max_use=20

127.0.0.1:10025 inet    n       -       -       -       -       smtpd
        -o content_filter=
        -o local_recipient_maps=
        -o relay_recipient_maps=
        -o smtpd_restriction_classes=
        -o smtpd_delay_reject=no
        -o smtpd_client_restrictions=permit_mynetworks,reject
        -o smtpd_helo_restrictions=
        -o smtpd_sender_restrictions=
        -o smtpd_recipient_restrictions=permit_mynetworks,reject
        -o smtpd_data_restrictions=reject_unauth_pipelining
        -o smtpd_end_of_data_restrictions=
        -o mynetworks=127.0.0.0/8
        -o smtpd_error_sleep_time=0
        -o smtpd_soft_error_limit=1001
        -o smtpd_hard_error_limit=1000
        -o smtpd_client_connection_count_limit=0
        -o smtpd_client_connection_rate_limit=0
        -o receive_override_options=no_header_body_checks,no_unknown_recipient_checks
```

Dem `pickup` Transport-Service fügen wir noch die folgenden Optionen hinzu, damit Spam-Report Nachrichten nicht als Spam gewertet werden:
```
-o content_filter=
-o receive_override_options=no_header_body_checks
```

Wir testen Clamav (und somit auch die Funktion von Amavis), indem wir eine Mail mit einer bekannten Antivirus-Testdatei namens EICAR verschicken: 
```
echo "Test email with EICAR" | mail -s "Test Email" -A eicar.txt robyn.koelle@psa-team02.cit.tum.de
```

Der Log bestätigt, dass die Mail blockiert wurde:
```
2024-09-06T21:59:54.872456+00:00 vmpsateam02-01 amavis[48018]: (48018-02) Blocked INFECTED (Eicar-Signature) {DiscardedInbound,Quarantined}, [192.168.2.2]:47128 <root@vmpsateam02-02.psa-team02.cit.tum.de> -> <robyn.koelle@psa-team02.cit.tum.de>, quarantine: S/virus-SAW35wmwyoTa, Queue-ID: A1CD1A5ABD, Message-ID: <1725667188.573865.13440.nullmailer@vmpsateam02-02>, mail_id: SAW35wmwyoTa, Hits: -, size: 1226, 165 ms
```

