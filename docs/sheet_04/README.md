# Aufgabenblatt 4

ℹ️ Unsere Dokumentation verweist häufig auf unser Ansible-Repository.
Daher empfiehlt es sich, die Dokumentation in unserem Repository zu lesen:
[https://github.com/robynkoelle/sysadmin-ansible](https://github.com/robynkoelle/sysadmin-ansible).

## Webserver

Wir installieren `nginx` mit apt.
Die `/etc/nginx/nginx.conf` ist in unserer `nginx`-Rolle hinterlegt.

Wir entfernen die default-Page durch Löschen des Symlinks `/etc/nginx/sites-enabled/default` und der Datei `/etc/nginx/sites-enabled/default`.

## Home Pages, Statische Dateien, FastCGI

Wir erstellen die Deployment-Rollen `deploy-early-bird.psa-team02.cit.tum.de`,`deploy-bearly-ird.psa-team02.cit.tum.de`, und`deploy-www.psa-team02.cit.tum.de`.

Die Rolle kopiert `/var/www/early-bird/index.html` rüber, und gibt owner / group an `www-data`.
Dann konfigurieren wir nginx (die vollständigen Konfigurationsdateien sind immer in der jeweiligen Deployment-Rolle dokumentiert):

### HTTPS Rewrite
```text
server {
    listen 80;
    server_name {{ deploy.nginx.domain }};
    return 301 https://$host$request_uri;
}
```

### Domain-Name und SSL
```text
server {
    listen 443 ssl;
    server_name {{ deploy.nginx.domain }};
    ssl_certificate /etc/nginx/ssl/{{ deploy.nginx.domain }}.crt;
    ssl_certificate_key /etc/nginx/ssl/{{ deploy.nginx.domain }}.key;
    # ...
}
```

### Root-location für die zurückgegebenen Daten angeben:
```text
    location / {
        root {{ deploy.nginx.root }};
    }
```

### Fast-CGI konfigurieren:
```text
    location ~ ^/~([^/]+)/cgi-bin/(.*)$ {
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME /home/$1/.cgi-bin/$2;
        fastcgi_pass unix:/var/run/fcgiwrap-$1.socket;
    }
```
Wir nutzen eine Regex, die Pfade zu den jeweiligen `cgi-bin` der User matcht.
Mit `fastcgi_pass` leiten wir den Request dann an einen User-spezifischen Socket weiter.
Damit dies funktioniert, konfigurieren wir unseren Server wie in der `fastcgiwrap`-Rolle beschrieben.
Wir installieren `fastcgiwrap` und `spawn-fcgi` mit `apt`.
Dann legen wir für jeden User einen Systemd-Service an:
```text
[Unit]
Description=FCGI Wrapper for user {{ item.name }}

[Service]
# Forking because spawn-fcgi spawns a child process.
# We do not want to call ExecStop immediately after successfully creating the child process.
Type=forking
# Note: /usr/sbin/fcgiwrap path must be absolute.
ExecStart=spawn-fcgi -s /var/run/fcgiwrap-{{ item.name }}.socket -U www-data -G www-data -u {{ item.uid }} -C 1 /usr/sbin/fcgiwrap
ExecStop=rm -f /var/run/fcgiwrap-{{ item.name }}.socket

[Install]
WantedBy=multi-user.target
```
Der Service spawnt den FCGI-Socket für den gegebenen User, und setzt die benötigten Permissions (`www-data` muss auf den Socket zugreifen können).
Wir enablen den Service, damit er bei jedem Boot automatisch startet.
Beim Stopp des Service wird der jeweilige Socket auch wieder aufgeräumt.

### Statische User-Inhalte

```text
    location ~ ^/~([^/]+)(.*)$ {
        set $path $2;
        if ($path = "") {
            set $path "/index.html";
        }
        alias /home/$1/.html-data$path;
    }
```
Hier nutzen wir (wie bei FCGI) wieder eine Regex, um den Pfad auf das Home Directory des Users zu matchen.
Mit einem `alias` verweisen wir dann auf die angefragte Datei.

### Website live schalten

Um die Website live zu schalten, kopieren wir die nginx-Config in `/etc/nginx/sites-available`, und kreieren einen Symlink von `/etc/nginx/sites-enabled/<...>` darauf (und laden den `nginx`-Service mit `systemctl` neu).
Wir haben selbst-signierte Zertifikate genutzt, die wir auch in der jeweiligen Rolle abgelegt haben.
Der jeweilige Key ist mit `ansible-vault` verschlüsselt.

Die Deployments für die anderen Domains sind analog (aber ohne FastCGI und die statischen Dateien - siehe in den jeweiligen Rollen).
Die verschiedenen nginx-Konfigurationen lauschen auf jeweils andere Domains, und verweisen auf jeweils verschiedene Inhalte - somit sind die drei Websites unabhängig.
Jede Website hat einen anderen Inhalt:
- `early-bird`: "Hello from early-bird!"
- `www`: "Hello from team02!"
- `bearly-ird`: "Hello from bearly-ird!"
 
## DNS

Zunächst fügen wir unserer `vmpsateam02-01` eine weitere IP-Adresse (`192.168.2.3`) auf dem Interface `enp0s8` hinzu.
Hierfür müssen wir nur unsere `host_vars/vmpsateam02-01.yml` anpassen, und die `network_interfaces`-Rolle neu ausführen.

Dann erweitern wir die `db.psa-team02.cit.tum.de` für `bind9` (und auch die jeweiligen Reverse-Lookups):
```text
www             IN      CNAME   early-bird
early-bird      IN      A       192.168.2.1
late-worm       IN      A       192.168.2.2
bearly-ird      IN      A       192.168.2.3
```
Die relevanten, aktuellen und vollständigen Dateien sind in der `dns`-Rolle dokumentiert.

## Logs 

Weiter oben haben wir bereits die `nginx.conf` erwähnt.
Hier konfigurieren wir das Log-Format:

```text
    log_format no_ip '$remote_user [$time_local] '
                     '"$request" $status $body_bytes_sent '
                     '"$http_referer" "$http_user_agent"';

	access_log /var/log/nginx/access.log no_ip;
```
Mit dieser Konfiguration werden wir den Anforderungen des Aufgabenblatts hinsichtlich Logs gerecht.

Wir installieren `logrotate` mit apt (siehe `logrotate`-Rolle).
In der `nginx`-Rolle konfigurieren wir die nginx-spezifischen Log-Rotations.
Die Konfigurationsdatei `/etc/logrotate.d/nginx` ist ebenfalls in der `nginx`-Rolle zu sehen.

- Zugriff-Logs (/var/log/nginx/access.log):
    - Logs werden täglich rotiert.
    - Die letzten 5 Rotationen werden aufbewahrt.
    - Leere Logs werden ignoriert. 
    - Die Logs werden komprimiert, aber die Komprimierung wird um eine Rotation verzögert. 
    - copytruncate wird verwendet, um die Datei nach dem Kopieren zu leeren. 
    - Alte Logs werden in {{ nginx.old_logs_location }} verschoben. 
    - Neue Logs werden mit den Rechten 0640 und den Eigentümern www-data und adm erstellt. 
- Error-Logs (/var/log/nginx/error.log):
    - Logs werden täglich rotiert.
    - Nur die letzte Rotation wird aufbewahrt.
    - Leere Logs werden ignoriert.
    - Die Logs werden komprimiert, wobei die Komprimierung um eine Rotation verzögert wird.
    - copytruncate wird auch hier verwendet.
    - Alte Logs werden in {{ nginx.old_logs_location }} verschoben.
    - Neue Logs werden ebenfalls mit den Rechten 0640 und den Eigentümern www-data und adm erstellt.
