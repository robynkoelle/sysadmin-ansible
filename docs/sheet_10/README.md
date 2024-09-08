# Aufgabenblatt 10: Dienstüberwachung

## Nagios

Wir nutzen Nagios als Dienstüberwachungsprogramm.
Nagios verwendet standardmäßig den apache2-Webserver.
Obwohl wir als primären Webserver nginx verwenden, installieren wir apache2 auf `vmpsateam02-01` mit apt.
Wir passen aber die Ports in `/etc/apache2/ports.conf` an, sodass apache2 auf die Ports `8080` bzw. `8443` hört (siehe in der [apache2-Rolle](../../ansible/roles/apache2).

Wir richten über die VirtualBox GUI eine Portweiterleitung ein, damit wir später von außen das Nagios-Webinterface aufrufen können: `60205` -> `8080`.

Ebenso erlauben wir eingehenden Traffic auf Port `8080` in iptables.


