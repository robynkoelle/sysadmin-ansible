# Aufgabenblatt 10: Dienstüberwachung

## Nagios

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
