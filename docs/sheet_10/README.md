# Aufgabenblatt 10

ℹ️ Unsere Dokumentation verweist häufig auf unser Ansible-Repository.
Daher empfiehlt es sich, die Dokumentation in unserem Repository zu lesen:
[https://github.com/robynkoelle/sysadmin-ansible](https://github.com/robynkoelle/sysadmin-ansible).

## Nagios

Zu unserem Nagios: [http://131.159.74.56:60205/nagios/](http://131.159.74.56:60205/nagios/)
Die Login-Credentials sind auf `192.168.2.1` unter `/root`.

Wir nutzen Nagios als Dienstüberwachungsprogramm.
Nagios verwendet standardmäßig den apache2-Webserver.
Obwohl wir als primären Webserver nginx verwenden, installieren wir apache2 auf `vmpsateam02-01` mit apt.
Wir passen aber die Ports in `/etc/apache2/ports.conf` an, sodass apache2 auf die Ports `8080` bzw. `8443` hört (siehe in der [apache2-Rolle](../../ansible/roles/apache2).

Wir richten über die VirtualBox GUI eine Portweiterleitung ein, damit wir später von außen das Nagios-Webinterface aufrufen können: `60205` -> `8080`.

Ebenso erlauben wir eingehenden Traffic auf Port `8080` in iptables.

Wir installieren den Nagios auf `vmpsateam02-01` mittels der Ansible-Rolle [nagios](../../ansible/roles/nagios).
Von dort aus wollen wir auch `vmpsateam02-02` monitoren, weshalb wir diese mit der [nagios-client-Rolle](../../ansible/roles/nagios-client) konfigurieren.

### Hauptserver

Auf `vmpsateam02-01` installieren wir zunächst Nagios, indem wir das Paket herunterladen und kompilieren.
Zunächst benötigen wir dependencies, die wir mit `apt` installieren:
```
    - autoconf
    - gcc
    - libc6
    - make
    - wget
    - unzip
    - apache2
    - php
    - libapache2-mod-php
    - libgd-dev
    - openssl
    - libssl-dev
```

Anschließend kompilieren und installieren wir Nagios wie in der Rolle unter `install.yml` beschrieben:
```
- name: download source
  get_url:
    url: "https://assets.nagios.com/downloads/nagioscore/releases/nagios-{{ nagios.version }}.tar.gz"
    dest: /tmp/nagioscore.tar.gz

- name: uncompress source
  shell: 
    cmd: "tar xzf nagioscore.tar.gz"
    chdir: "/tmp/"

- name: compile 
  shell:
    cmd: "./configure --with-httpd-conf=/etc/apache2/sites-enabled && make all"
    chdir: "/tmp/nagios-{{ nagios.version }}/"

- name: create user and group
  shell:
    cmd: "make install-groups-users"
    chdir: "/tmp/nagios-{{ nagios.version }}/"

- name: install binaries
  shell:
    cmd: "make install"
    chdir: "/tmp/nagios-{{ nagios.version }}/"

- name: install service / daemon
  shell:
    cmd: "make install-daemoninit"
    chdir: "/tmp/nagios-{{ nagios.version }}/"

- name: install command mode
  shell:
    cmd: "make install-commandmode"
    chdir: "/tmp/nagios-{{ nagios.version }}/"

- name: install config files 
  shell:
    cmd: "make install-config"
    chdir: "/tmp/nagios-{{ nagios.version }}/"

- name: install apache config files 
  shell:
    cmd: "make install-webconf"
    chdir: "/tmp/nagios-{{ nagios.version }}/"
```

Danach müssen wir noch die Module `cgi` und `rewrite` mit `a2enmod` aktivieren.

Wir erzeugen den Admin-User mit folgendem Kommando:
```
sudo htpasswd -cb /usr/local/nagios/etc/htpasswd.users nagiosadmin {{ nagios.admin_password }}
```

Dann können wir den nagios-Service starten:
```
systemctl start nagios.service
```

Somit ist das Webinterface vom Internet aus über [http://131.159.74.56:60205/nagios/](http://131.159.74.56:60205/nagios/) erreichbar.

Analog zu nagios selbst, installieren wir uns `nagios-plugins`, indem wir die Source von `https://github.com/nagios-plugins/nagios-plugins/archive/release-{{ nagios.plugins_version }}.tar.gz` herunterladen, und kompilieren.
Hierfür benötigen wir ebenfalls dependencies.
Das alles ist unter `plugins.yml` in der Rolle dokumentiert.
Für weitere Plugins, die hier nicht enthalten sind (wie z.B. `check_pgsql`), installieren wir noch `nagios-plugins` mit apt.

Zusätzlich installieren wir uns (wieder analog) NRPE (`https://github.com/NagiosEnterprises/nrpe/releases/download/nrpe-4.1.1/nrpe-4.1.1.tar.gz`), um Checks auf anderen VMs über das Netzwerk ausführen zu können. 

Die `config.yml` in der Ansible-Rolle beschreibt, wie wir Nagios konfigurieren.
Wir definieren unsere Hosts (der einzige remote-Host ist in unserem Fall `vmpsateam02-02`) in `/usr/local/nagios/etc/hosts.cfg`, und unsere Services in `/usr/local/nagios/etc/services.cfg`.

Diese Dateien müssen wir in der `/usr/local/nagios/etc/nagios.cfg` importieren:
```
cfg_file=/usr/local/nagios/etc/hosts.cfg
cfg_file=/usr/local/nagios/etc/services.cfg
```

Unsere `hosts.cfg`:
```
define host {
    use                 linux-server
    host_name           vmpsateam02-02
    alias               VM02
    address             192.168.2.2
    max_check_attempts  5
    check_period        24x7
    notification_interval 30
    notification_period 24x7
}
```

Zusätzlich müssen wir noch den Command für `check_nrpe` hinzufügen, indem wir die `/usr/local/nagios/etc/objects/commands.cfg` editieren:
```
define command {
    command_name check_nrpe
    command_line $USER1$/check_nrpe -H $HOSTADDRESS$ -c $ARG1$
}
```

Damit die remote-Checks funktionieren, müssen wir zunächst `vmpsateam02-02` entsprechend konfigurieren.

### Sekundäre Nagios Server

Mit der [nagios-client-Rolle](../../ansible/roles/nagios-client) konfigurieren wir `vmpsateam02-02` so, dass unser Nagios-Hauptserver Checks auf dort ausführen kann.

Wir installieren mit `apt` die Pakete `nagios-nrpe-server`, `nagios-plugins`.
Dann müssen wir noch die IP-Adresse von `vmpsateam02-01` als `allowed_host` konfigurieren:
```
- name: allow hosts
  lineinfile:
    line: "allowed_hosts={{ nagios_client.allowed_hosts }}"
    path: /etc/nagios/nrpe.cfg
    regexp: "^allowed_hosts="
```

Der `nagios-nrpe-server` läuft auf Port `5666`, also schalten wir eingehenden Traffic von `192.168.2.1` an diesen Port in iptables frei.

Auf `vmpsateam02-01` prüfen, dass NRPE an `vmpsateam02-02` funktioniert:
```
root@vmpsateam02-01:/usr/local/nagios/etc# /usr/local/nagios/libexec/check_nrpe -H 192.168.2.2
NRPE v4.1.0
```

Die Ausgabe der Versionsnummer von NRPE bestätigt die Funktion.

## Konfigurieren der Checks 

Wir definieren die auszuführenden Checks für den Nagios-Server in `/usr/local/nagios/etc/objects/localhost.cfg`,
und für `vmpsateam02-02` in `/usr/local/nagios/etc/services.cfg`.

### Anzeigen des verfügbaren Speichers

Bereits von Nagios voreingestellt in der `localhost.cfg`.
Hierfür wird der ebenfalls vorkonfigurierte (in `/usr/local/nagios/etc/objects/commands.cfg`) Command `check_disk` verwendet. 

### Anzeigen der Länge der Mail-Queue
Kommando definieren in `commands.cfg`:

```text
 define command {
    command_name    check_mailq
    command_line    /usr/lib/nagios/plugins/check_mailq -w 50 -c 100
}  
```

Service definieren in `localhost.cfg` (Postfix läuft auf `vmpsateam02-01`):

```text
define service {
use                 local-service
host_name           localhost
service_description Mail Queue Length
check_command       check_mail_queue
}
```

### Betriebssystem

Ping und Load sind hier sinnvolle Checks.

Lokale Maschine pingen (bereits vorkonfiguriert):
```text
define service {
use                     local-service           
host_name               localhost
service_description     PING
check_command           check_ping!100.0,20%!500.0,60%
}
```

Lokalen load prüfen (bereits vorkonfiguriert): 
```text
define service {
use                     local-service           
host_name               localhost
service_description     Current Load
check_command           check_local_load!5.0,4.0,3.0!10.0,6.0,4.0
}
```

Analog die Kommandos via NRPE ausführen:
```text
define service {
    use                     generic-service
    host_name               vmpsateam02-02
    service_description     CPU Load
    check_command           check_nrpe!check_load
}
define service {
    use                     generic-service
    host_name               vmpsateam02-02
    service_description     Ping
    check_command           check_nrpe!check_ping
}
```

Damit `check_ping` via NRPE funktioniert, müssen wir in `/etc/nagios/nrpe.cfg` auf dem Remote Host den Command definieren:
```text
command[check_ping]=/usr/lib/nagios/plugins/check_ping -H 127.0.0.1 -w 100.0,20% -c 500.0,60% -p 5
```
Der `check_load`-Command war bereits vordefiniert.

In den folgenden Punkten gehen wir analog vor.
Damit die Dokumentation übersichtlich bleibt, verzichten wir von jetzt an darauf, den Boilerplate für Commands und Services zu wiederholen.

Auf beiden VMs:
- `check_swap`, um den genutzten Swap zu überwachen
- `check_procs`, um die Anzahl der laufenden Prozesse zu überwachen
- `check_users`, um die Anzahl der eingeloggten Nutzer zu überwachen
- `check_local_disk` bzw. `check_disk_root`, um den freien Speicherplatz zu überwachen

### Netzwerk

Hierfür verwenden wir wieder `check_ping`, aber statt dem localhost pingen wir
- Die Adresse unseres Routers in den jeweiligen Verbindungsnetzen (nur auf `vmpsateam02-01`)
- Die jeweils eigene IP-Adresse unserer VMs im Team-Netz
- Die jeweils andere IP-Adresse unserer VMs im Team-Netz

### DNS

- Mit `check_procs` bzw. `check_local_procs` prüfen, dass Bind9 läuft (nur auf `vmpsateam02-01`)
- Mit `check_dns` prüfen, dass `early-bird.psa-team02.cit.tum.de auf `192.168.2.1` resolvet

Den `check_dns` Command fügen wir wie folgt der `commands.cfg` hinzu:
```text
define command {
    command_name    check_dns
    command_line    /usr/lib/nagios/plugins/check_dns -H $ARG1$ -a $ARG2$
}
```

Für die Übersichtlichkeit lassen wir auch weitere Command-Definitionen in den folgenden Abschnitten aus.
Die jeweiligen Config-Dateien in unserer `nagios`- bzw. `nagios-client`-Rolle dienen als Dokumentation.

###  DHCP

- Mit `check_dhcp` überprüfen wir die Verfügbarkeit unseres DHCP Servers im Netzwerk (über dessen IP)

### Webserver

- Mit `check_http` überprüfen wir die Verfügbarkeit unseres Webservers (HTTP)
- Mit der `-p 443` und `-S` überprüfen wir HTTPS

### Datenbank

- Mit `check_pgsql` überprüfen wir die Verfügbarkeit unserer WikiJS-Datenbank
- Idealerweise würden wir hier auch explizit die Verfügbarkeit der Datenbank testen, die wir an Team 1 bereitstellen. Aus Security-Gründen verwalten wir aber nur das initiale Passwort für Team 1, nicht das aktuelle. Die generelle Funktionalität von Postgres wird aber durch den obigen Command bereits getestet. 

Die benötigten Credentials schreiben wir in die `localhost.cfg`.
Damit nur der nagios-Nutzer diese lesen kann, geben wir der Datei die Permissions 0600 (und owner/group: nagios).

### Web-Applikation

Unsere WikiJS Web-App läuft in einem Docker-Container auf Port 3000, den wir auf den Port 8081 unseres Systems mappen.
Wir machen also einen `check_http` auf `8081`.

### Fileserver

Zusätzlich zur Voreinstellung, die die Größe der Root-Partition überwacht, überwachen wir explizit noch den Root unseres Fileservers `/mnt/raid`:

```text
define service {
    use                 local-service
    host_name           localhost
    service_description Disk Space Fileserver
    check_command       check_local_disk!20%!10%!/mnt/raid
}
```
Man könnte natürlich noch zusätzliche Plugins installieren, die explizit Samba und NFS testen.
Dies lassen wir hier aus, da es vom Prinzip her sehr ähnlich zu den obigen Postgres-Checks funktioniert.

### LDAP

- Wir nutzen `check_ldap`, um uns mit unserem LDAP-Directory zu verbinden

### Mail

- Anzeigen der Länge der Mail Queue (weiter oben dokumentiert)
- Mit `check_tcp` prüfen, ob Postfix (Port 25) und Dovecot (Port 143) jeweils da sind

## Benachrichtigungen

Nagios stellt standardmäßig folgende Commands bereit:

```text
define command {
    command_name    notify-host-by-email
    command_line    /usr/bin/printf "%b" "***** Nagios *****\n\nNotification Type: $NOTIFICATIONTYPE$\nHost: $HOSTNAME$\nState: $HOSTSTATE$\nAddress: $HOSTADDRESS$\nInfo: $HOSTOUTPUT$\n\nDate/Time: $LONGDATETIME$\n" | /usr/bin/mail -s "** $NOTIFICATIONTYPE$ Host Alert: $HOSTNAME$ is $HOSTSTATE$ **" $CONTACTEMAIL$
}



define command {
    command_name    notify-service-by-email
    command_line    /usr/bin/printf "%b" "***** Nagios *****\n\nNotification Type: $NOTIFICATIONTYPE$\n\nService: $SERVICEDESC$\nHost: $HOSTALIAS$\nAddress: $HOSTADDRESS$\nState: $SERVICESTATE$\n\nDate/Time: $LONGDATETIME$\n\nAdditional Info:\n\n$SERVICEOUTPUT$\n" | /usr/bin/mail -s "** $NOTIFICATIONTYPE$ Service Alert: $HOSTALIAS$/$SERVICEDESC$ is $SERVICESTATE$ **" $CONTACTEMAIL$
}
```

Diese verwenden wir in unserer `contacts.cfg`:
```text
define contact {

contact_name            nagiosadmin             ; Short name of user
use                     generic-contact         ; Inherit default values from generic-contact template (defined above)
alias                   Nagios Admin            ; Full name of user
email                   robyn.koelle@psa-team02.cit.tum.de
service_notification_commands notify-service-by-email
host_notification_commands notify-host-by-email
}
```

Auf genau dieselbe Weise kann man auch alternative Benachrichtigungswege nutzen, wie zum Beispiel Slack-Hooks.
Im Rahmen des Praktikums ist eine simplere Lösung angebracht: wir schreiben einfach in eine Datei.
Hierzu definiert man sich einen Command:

```text
define command {
    command_name    notify-host-by-file
    command_line    /usr/bin/printf "%b" "***** Nagios *****\n\nNotification Type: $NOTIFICATIONTYPE$\nHost: $HOSTNAME$\nState: $HOSTSTATE$\nAddress: $HOSTADDRESS$\nInfo: $HOSTOUTPUT$\n\nDate/Time: $LONGDATETIME$\n" > /var/lib/nagios/notifications/host-$LONGDATETIME$
}

define command {
    command_name    notify-service-by-file
    command_line    /usr/bin/printf "%b" "***** Nagios *****\n\nNotification Type: $NOTIFICATIONTYPE$\n\nService: $SERVICEDESC$\nHost: $HOSTALIAS$\nAddress: $HOSTADDRESS$\nState: $SERVICESTATE$\n\nDate/Time: $LONGDATETIME$\n\nAdditional Info:\n\n$SERVICEOUTPUT$\n" > /var/lib/nagios/notifications/service-$LONGDATETIME$
}
```

Der Command gibt den gleichen Content aus, schreibt ihn aber einfach in `/var/lib/nagios/notifications/...`.
Diesen Ordner haben wir angelegt, damit nagios darin Dateien schreiben kann.

In `contacts.cfg` geben wir also an:
```text
...
service_notification_commands notify-service-by-email,notify-service-by-file
host_notification_commands notify-host-by-email,notify-host-by-file
...
```

In den Services konfigurieren wir dann:
```text
notification_interval   60
notification_options    w,u,c,r
contact_groups          admins
```

Damit kriegt die contact group `admins` (zu der unser Contact gehört) `warning`, `unknown`, `critical`, und `recovery` Benachrichtigungen.

Ein Blick ins Postfach (Maildir) des Admins verifiziert, dass wir von Nagios benachrichtigt werden:
```text
Subject: ** PROBLEM Service Alert: VM02/Check Webserver HTTPS is CRITICAL **
To: <robyn.koelle@psa-team02.cit.tum.de>
User-Agent: mail (GNU Mailutils 3.16)
Date: Sun, 15 Sep 2024 12:12:22 +0000
Message-Id: <20240915121222.5BF21A65B5@psa-team02.cit.tum.de>
From: nagios@vmpsateam02-01

***** Nagios *****

Notification Type: PROBLEM

Service: Check Webserver HTTPS
Host: VM02
Address: 192.168.2.2
State: CRITICAL

Date/Time: Sun Sep 15 12:12:22 UTC 2024

Additional Info:

connect to address 127.0.0.1 and port 443: Connection refused
```
