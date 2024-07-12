# Aufgabenblatt 3

## DNS 

Wir installieren Bind9 für unser Domain Name System auf unserem Router `vmpsateam02-01`.
Hierfür installieren wir die Pakete `bind9`, `bind9utils`, und `bind9-doc`.

Alle für Bind9 relevanten Konfigurationsdateien legen wir unter `etc/bind` ab, und starten den Service anschließend neu, um die Konfiguration zu übernehmen.

In der [named.conf.options](../../ansible/roles/dns/templates/vmpsateam02-01/etc/bind/named.conf.options)-Datei spezifizieren wir unter anderem:
- Eine `psa` access control list (`acl`): Adressen / Subnetze, für die wir z.B. `allow-query` konfigurieren können ("von wo" Anfragen erlaubt sind).
- Die gegebenen Forwarder-Adressen für Anfragen, die an keines der Teams gehen

In [db.psa-team02.cit.tum.de](../../ansible/roles/dns/templates/vmpsateam02-01/etc/bind/db.psa-team02.cit.tum.de)
weisen wir jeder der auf unseren VMs aktiven IP-Adressen einen Namen zu, und verwalten weitere DNS Einträge (wie z.B. CNAMEs).
Den Reverse-Lookup gewährleisten wir durch unsere Konfiguration in [db.2.168.192](../../ansible/roles/dns/templates/vmpsateam02-01/etc/bind/db.2.168.192) und dem Folgenden:

In [named.conf.local](../../ansible/roles/dns/templates/vmpsateam02-01/etc/bind/named.conf.local) konfigurieren wir:
- Den Zonentransfer zu einem anderen Team: eine Zone vom Typ `master`, die unter `allow-transfer` die Adresse(n) eines anderen Teams für den Transfer der  [db.psa-team02.cit.tum.de](../../ansible/roles/dns/templates/vmpsateam02-01/etc/bind/db.psa-team02.cit.tum.de) zulässt.
- Unsere Reverse-Zone, die [db.2.168.192](../../ansible/roles/dns/templates/vmpsateam02-01/etc/bind/db.2.168.192) referenziert.
- Unsere Slaves für ein anderes Team: Zonen vom Typ `slave`, die einen `master` eines anderes Teams haben.
- Unsere Forwarders: Zonen vom Typ `forward` für Anfragen an die Zonen der jeweils anderen Teams. 

> ⚠️  TODO: zweites Team für Zonentransfer

# DHCP

Wir nutzen Kea für unseren DHCP-Server, und installieren dafür das Paket `kea-dhcp4-server`.
Analog zu Bind9 legen wir unsere Konfigurationsdatei unter [/etc/kea/kea-dhcp4.conf](../../ansible/roles/dhcp/templates/vmpsateam02-01/etc/kea/kea-dhcp4.conf) ab, und starten den Systemd-Service neu. 

In der Datei konfigurieren wir unter anderem:
- `interfaces-config`: Das Interface, und die IP-Adresse, auf die der DHCP-Server hört. 
- Das Subnetz, und die möglichen Adressen, die der DHCP innerhalb des Subnetzes vergeben kann (unter `subnet4`: `subnet` und `pools`)
- Weitere Optionen: den DNS-Server, den Domänennamen, den Router für das Netzwerk (`option-data`).
- Für die Web-Proxy spezifizieren wir eine Option unter `option-def` mit dem Code `252` (siehe z.B. [hier](https://serverfault.com/questions/707586/is-it-possible-to-configure-proxy-setting-through-dhcp)).
- Die statischen Routen zu den Subnetzen der anderen Teams konfigurieren wir auf ähnliche Weise mit dem Code 121 (siehe z.B. [hier]()). 
- Feste IP-Adressen und Hostnames für gegebene Ethernet-Adressen (unter `reservations`).

