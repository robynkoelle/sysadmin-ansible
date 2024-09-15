# Aufgabenblatt 2

ℹ️ Unsere Dokumentation verweist häufig auf unser Ansible-Repository.
Daher empfiehlt es sich, die Dokumentation in unserem Repository zu lesen:
[https://github.com/robynkoelle/sysadmin-ansible](https://github.com/robynkoelle/sysadmin-ansible).

## Netzwerk

### Verbindung zwischen VMs

Unser Team hat das Subnetz `192.168.2.0/24`.
Innerhalb unseres Subnetzes haben wir die folgenden Adressen:
- `vmpsateam02-01: 192.168.2.1`
- `vmpsateam02-02: 192.168.2.2`

Hinzufügen der Adresse via `ip`:
- Auf `vmpsateam02-01`: `ip addr add 192.168.2.1/24 dev enp0s8`
- Auf `vmpsateam02-02`: `ip addr add 192.168.2.2/24 dev enp0s8`

Änderungen auf dem enp0s8 Interface aktiv schalten:

`ip link set enp0s8 up`

Anschließend können sich die beiden VMs gegenseitig via `192.168.2.1` bzw. `192.168.2.2` pingen.

Um die Konfiguration zu persistieren, sodass sie auch nach Reboots noch funktioniert, verwenden wir `netplan`.
Hierfür kopieren wir unsere Template-Datei [00-netplan.yaml](..%2F..%2Fansible%2Froles%2Fnetplan%2Ftemplates%2Fetc%2Fnetplan%2F00-netplan.yaml),
deaktivieren `cloud-init` und den zugehörigen vorinstallierten Netplan (was bei Ubuntu vorkonfiguriert war),
und aktivieren die neue Konfiguration mit `netplan apply`.
Unsere Konfiguration dient gleichzeitig auch als Dokumentation.
Die entsprechenden Variablen für die beiden Netplans sind in den Host Variablen
[vmpsateam02-01.yml](..%2F..%2Fansible%2Finventory%2Fhost_vars%2Fvmpsateam02-01.yml)
und
[vmpsateam02-02.yml](..%2F..%2Fansible%2Finventory%2Fhost_vars%2Fvmpsateam02-02.yml)
(jeweils unter dem Key `network_interfaces`) übersichtlich dokumentiert.
Der finale, resultierende Netplan ist im nächsten Abschnitt aufgeführt.

### Verbindung zwischen Subnetzen

Für die Verbindung mit den anderen Teams nutzen wir `vmpsateam02-01` als Router.
Dieser braucht Verbindungssubnetze zu den jeweiligen Routern der anderen Teams.
Wir spezifizieren für jedes der festgelegten Subnetze eine IP-Adresse für unseren Router,
über die die Kommunikation mit den anderen Routern stattfindet.

Um beispielsweise eine Verbindung zu Team 1 herzustellen, benötigen wir folgende Kommandos auf dem Router:
- IP-Adresse unseres Routers im 21er-Subnetz erstellen: `ip addr add 192.168.21.2/24 dev enp0s8`
- Verbindungen in das Subnetz von Team 1 an den Router von Team 1 im 21er-Subnetz leiten: `ip route add 192.168.1.0/24 via 192.168.21.1`

Anmerkung: jedes Team X hat ein Subnetz mit jedem anderen Team Y.
Wir bezeichnen dies als Subnetz XY, wobei X > Y.
Der Router von Team X hat in diesem Subnetz die Adresse `192.168.XY.2`,
der von Team Y hat die Adresse `192.168.XY.1`.

Nun benötigen die anderen VMs in unserem eigenen Subnetz noch IP-Adressen,
und die Konfiguration, dass Anfragen an die Subnetze anderer Teams über unseren Router gehen sollen.
Für unsere `vmpsateam02-02`:
- `ip addr add 192.168.2.2/24 dev enp0s8`
- `ip route add 192.168.1.0/24 via 192.168.2.1` # Team 1
- `ip route add 192.168.3.0/24 via 192.168.2.1` # Team 3
- ...

Dies haben wir ebenfalls mit `netplan` persistiert, und mit unseren `host_vars` dokumentiert.

Die finale Konfiguration für den Router `vmpsateam02-01`:
```yaml
network:
  version: 2
  ethernets:
    enp0s8:
        dhcp4: False
        addresses:
          - 192.168.2.1/24
          - 192.168.21.2/24
          - 192.168.32.1/24
          - 192.168.42.1/24
          - 192.168.52.1/24
          - 192.168.62.1/24
          - 192.168.72.1/24
          - 192.168.82.1/24
          - 192.168.92.1/24
          - 192.168.102.1/24
        routes:
          - to: 192.168.1.0/24
            via: 192.168.21.1
          - to: 192.168.3.0/24
            via: 192.168.32.2
          - to: 192.168.4.0/24
            via: 192.168.42.2
          - to: 192.168.5.0/24
            via: 192.168.52.2
          - to: 192.168.6.0/24
            via: 192.168.62.2
          - to: 192.168.7.0/24
            via: 192.168.72.2
          - to: 192.168.8.0/24
            via: 192.168.82.2
          - to: 192.168.9.0/24
            via: 192.168.92.2
          - to: 192.168.10.0/24
            via: 192.168.102.2
    enp0s3:
        dhcp4: True
```

Die finale Konfiguration für die VM `vmpsateam02-02`:
```yaml
network:
  version: 2
  ethernets:
    enp0s8:
        dhcp4: False
        addresses:
          - 192.168.2.2/24
        routes:
          - to: 192.168.1.0/24
            via: 192.168.2.1
          - to: 192.168.3.0/24
            via: 192.168.2.1
          - to: 192.168.4.0/24
            via: 192.168.2.1
          - to: 192.168.5.0/24
            via: 192.168.2.1
          - to: 192.168.6.0/24
            via: 192.168.2.1
          - to: 192.168.7.0/24
            via: 192.168.2.1
          - to: 192.168.8.0/24
            via: 192.168.2.1
          - to: 192.168.9.0/24
            via: 192.168.2.1
          - to: 192.168.10.0/24
            via: 192.168.2.1
    enp0s3:
        dhcp4: True
```
Mit `ip route` und `ip a` können wir die Konfiguration überprüfen.

## HTTP(S) Proxy

Wir konfigurieren eine HTTP(S) Proxy, indem wir die http_proxy und https_proxy environment Variablen
persistent unter /etc/environment konfigurieren:
[environment.yml](..%2F..%2Fansible%2Froles%2Fhttp-proxy%2Ftasks%2Fenvironment.yml).

Die Proxy geben wir als Group-Variable konsistent für all unsere VMs an:
[vmpsateam02.yml](..%2F..%2Fansible%2Finventory%2Fgroup_vars%2Fvmpsateam02.yml)
(unter dem Key `http_proxy`).

Die Inhalte der Datei werden beim Login übernommen und müssen deshalb nicht als Teil des Provisionings gesourcet werden.

## Firewall

Wir nutzen `iptables` für unsere Firewall.
Um unser Provisioning möglichst explizit zu machen,
und um die Konfiguration zu persistieren, schreiben wir eine `/etc/iptables/rules.v4` Datei, um unsere Regeln zu definieren.
Wir installieren `iptables-persistent` via `apt`, um die Regeln zu persistieren.

Hierfür verwenden wir wieder Templating:
[rules.v4](..%2F..%2Fansible%2Froles%2Fiptables%2Ftemplates%2Fetc%2Fiptables%2Frules.v4).
In der Datei dokumentieren wir genau mit Kommentaren, wozu welche Regel dient.
TODO: neu dokumentieren

Die jeweiligen Werte für die Regeln werden aus den Host-Variablen gelesen, die hier wieder als Dokumentation dienen sollen:
[vmpsateam02-01.yml](..%2F..%2Fansible%2Finventory%2Fhost_vars%2Fvmpsateam02-01.yml)
und
[vmpsateam02-02.yml](..%2F..%2Fansible%2Finventory%2Fhost_vars%2Fvmpsateam02-02.yml)
(jeweils unter dem Key `iptables`).

Da wir IPv6 zunächst nicht unterstützen wollen,
erstellen wir der Einfachheit halber analog eine minimale rules.v6 Datei,
die alles verbietet:
[rules.v6](..%2F..%2Fansible%2Froles%2Fiptables%2Ftemplates%2Fetc%2Fiptables%2Frules.v6)

Für die Kommunikation mit den Subnetzen der anderen Teams muss folgendes gelten:
- Der Router erlaubt outgoing traffic zu den jeweiligen Subnetzen
- Der Router erlaubt forwarding zwischen den jeweiligen Subnetzen in jeweils beide Richtungen
- Die VMs in unserem Subnetz erlauben outgoing traffic zu den jeweiligen Subnetzen

Die finale Konfiguration für die Router-Firewall (`vmpsateam02-01`):
```
*raw
:PREROUTING ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]

# Disable connection tracking for HTTP(S)
-A PREROUTING -p tcp --dport 80 -j NOTRACK
-A OUTPUT -p tcp --sport 80 -j NOTRACK
-A PREROUTING -p tcp --dport 443 -j NOTRACK
-A OUTPUT -p tcp --sport 443 -j NOTRACK
COMMIT

*filter

# Drop all incoming and outgoing traffic by default
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT DROP [0:0]

# Allow established connections
-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Allow incoming HTTP, HTTPS, and responses to the requests
-A INPUT -p tcp --dport 80 -j ACCEPT
-A OUTPUT -p tcp --sport 80 -j ACCEPT
-A INPUT -p tcp --dport 443 -j ACCEPT
-A OUTPUT -p tcp --sport 443 -j ACCEPT

# Allow SSH
-A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
-A OUTPUT -p tcp --sport 22 -m conntrack --ctstate ESTABLISHED -j ACCEPT

# Allow DNS for outbound queries
-A OUTPUT -p udp --dport 53 -j ACCEPT
-A OUTPUT -p tcp --dport 53 -j ACCEPT
-A INPUT -p udp --dport 53 -j ACCEPT
-A INPUT -p tcp --dport 53 -j ACCEPT

# Outgoing explicit allow
-A OUTPUT -d 131.159.0.0/16 -j ACCEPT
-A OUTPUT -d 192.168.2.0/24 -j ACCEPT
-A OUTPUT -d 192.168.1.0/24 -j ACCEPT
-A OUTPUT -d 192.168.3.0/24 -j ACCEPT
-A OUTPUT -d 192.168.4.0/24 -j ACCEPT
-A OUTPUT -d 192.168.5.0/24 -j ACCEPT
-A OUTPUT -d 192.168.6.0/24 -j ACCEPT
-A OUTPUT -d 192.168.7.0/24 -j ACCEPT
-A OUTPUT -d 192.168.8.0/24 -j ACCEPT
-A OUTPUT -d 192.168.9.0/24 -j ACCEPT
-A OUTPUT -d 192.168.10.0/24 -j ACCEPT
-A OUTPUT -d 141.30.62.23 -j ACCEPT
-A OUTPUT -d 141.30.62.22 -j ACCEPT
-A OUTPUT -d 141.30.62.25 -j ACCEPT
-A OUTPUT -d 141.30.62.26 -j ACCEPT
-A OUTPUT -d 141.30.62.24 -j ACCEPT
-A OUTPUT -d 185.125.190.39 -j ACCEPT
-A OUTPUT -d 91.189.91.83 -j ACCEPT
-A OUTPUT -d 185.125.190.36 -j ACCEPT
-A OUTPUT -d 91.189.91.81 -j ACCEPT
-A OUTPUT -d 91.189.91.82 -j ACCEPT

# Forward explicit allow
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.2.0/24 -d 192.168.1.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.1.0/24 -d 192.168.2.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.2.0/24 -d 192.168.3.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.3.0/24 -d 192.168.2.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.2.0/24 -d 192.168.4.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.4.0/24 -d 192.168.2.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.2.0/24 -d 192.168.5.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.5.0/24 -d 192.168.2.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.2.0/24 -d 192.168.6.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.6.0/24 -d 192.168.2.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.2.0/24 -d 192.168.7.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.7.0/24 -d 192.168.2.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.2.0/24 -d 192.168.8.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.8.0/24 -d 192.168.2.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.2.0/24 -d 192.168.9.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.9.0/24 -d 192.168.2.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.2.0/24 -d 192.168.10.0/24 -j ACCEPT
-A FORWARD -i enp0s8 -o enp0s8 -s 192.168.10.0/24 -d 192.168.2.0/24 -j ACCEPT

-A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow all ICMP traffic
-A INPUT -p icmp -j ACCEPT
-A OUTPUT -p icmp -j ACCEPT

# Allow loopback
-A INPUT -i lo -j ACCEPT
-A OUTPUT -o lo -j ACCEPT

COMMIT
```

Die finale Konfiguration für `vmpsateam02-02`:
```
*raw
:PREROUTING ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]

# Disable connection tracking for HTTP(S)
-A PREROUTING -p tcp --dport 80 -j NOTRACK
-A OUTPUT -p tcp --sport 80 -j NOTRACK
-A PREROUTING -p tcp --dport 443 -j NOTRACK
-A OUTPUT -p tcp --sport 443 -j NOTRACK
COMMIT

*filter

# Drop all incoming and outgoing traffic by default
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT DROP [0:0]

# Allow established connections
-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Allow incoming HTTP, HTTPS, and responses to the requests
-A INPUT -p tcp --dport 80 -j ACCEPT
-A OUTPUT -p tcp --sport 80 -j ACCEPT
-A INPUT -p tcp --dport 443 -j ACCEPT
-A OUTPUT -p tcp --sport 443 -j ACCEPT

# Allow SSH
-A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
-A OUTPUT -p tcp --sport 22 -m conntrack --ctstate ESTABLISHED -j ACCEPT

# Allow DNS for outbound queries
-A OUTPUT -p udp --dport 53 -j ACCEPT
-A OUTPUT -p tcp --dport 53 -j ACCEPT
-A INPUT -p udp --dport 53 -j ACCEPT
-A INPUT -p tcp --dport 53 -j ACCEPT

# Outgoing explicit allow
-A OUTPUT -d 131.159.0.0/16 -j ACCEPT
-A OUTPUT -d 141.30.62.23 -j ACCEPT
-A OUTPUT -d 141.30.62.22 -j ACCEPT
-A OUTPUT -d 141.30.62.25 -j ACCEPT
-A OUTPUT -d 141.30.62.26 -j ACCEPT
-A OUTPUT -d 141.30.62.24 -j ACCEPT
-A OUTPUT -d 185.125.190.39 -j ACCEPT
-A OUTPUT -d 91.189.91.83 -j ACCEPT
-A OUTPUT -d 185.125.190.36 -j ACCEPT
-A OUTPUT -d 91.189.91.81 -j ACCEPT
-A OUTPUT -d 91.189.91.82 -j ACCEPT
-A OUTPUT -d 192.168.1.0/24 -j ACCEPT
-A OUTPUT -d 192.168.2.0/24 -j ACCEPT
-A OUTPUT -d 192.168.3.0/24 -j ACCEPT
-A OUTPUT -d 192.168.4.0/24 -j ACCEPT
-A OUTPUT -d 192.168.5.0/24 -j ACCEPT
-A OUTPUT -d 192.168.6.0/24 -j ACCEPT
-A OUTPUT -d 192.168.7.0/24 -j ACCEPT
-A OUTPUT -d 192.168.8.0/24 -j ACCEPT
-A OUTPUT -d 192.168.9.0/24 -j ACCEPT
-A OUTPUT -d 192.168.10.0/24 -j ACCEPT


-A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow all ICMP traffic
-A INPUT -p icmp -j ACCEPT
-A OUTPUT -p icmp -j ACCEPT

# Allow loopback
-A INPUT -i lo -j ACCEPT
-A OUTPUT -o lo -j ACCEPT

COMMIT
```

## Tests

Unser Skript führt mit `nmap` Scans nach allen Hosts der jeweiligen Subnets durch, um die Verbindungen mit `ping` zu überprüfen.
Es testet außerdem, ob das jeweilige Ziel via unserem Router erreicht wurde.
Es überprüft wesentliche Firewall-Regeln (z.B. "Can surf internet" oder "Cannot surf internet without proxy").
Außerdem gibt es die eigenen Adressen, Routen und die Firewall-Regeln aus:
[test_PSA_02.sh](..%2F..%2Ftest%2Ftest_PSA_02.sh)
