# Aufgabenblatt 5 

ℹ️ Unsere Dokumentation verweist häufig auf unser Ansible-Repository.
Daher empfiehlt es sich, die Dokumentation in unserem Repository zu lesen:
[https://github.com/robynkoelle/sysadmin-ansible](https://github.com/robynkoelle/sysadmin-ansible).

## Postgres

Wir nutzen für unsere Datenbank Postgresql und konfigurieren dies mit der `postgresql`-Rolle in unserem Repository.
Da das Paket in der zum Zeitpunkt der Bearbeitung der Aufgabe neuesten Postgres-Version (16) nicht direkt mit `apt` installierbar ist,
müssen wir erst das Repository hinzufügen.
Dafür benötigen wir die dependencies `ca-certificates` und `curl`, die wir mit `apt` installieren.

Wir laden den offiziellen Postgres PGP-Key herunter, und speichern ihn unter `/etc/apt/keyrings/postgres.asc`.
Dann fügen wir das Repository, signiert mit diesem Key, den apt-Sources hinzu:
```shell
echo "deb [signed-by=/etc/apt/keyrings/postgres.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
```

Nach einem `apt update` können wir das Paket `postgresql-16` installieren.
Wir starten den `systemd` Service namens `postgresql`.
Wir konfigurieren Postgres wie in der `/etc/postgresql/16/main/postgresql.conf` beschrieben (vgl. Datei in der `postgres`-Rolle).

In der `users.yml` in unserer `postgres`-Rolle legen wir die Nutzer via Ansible-Variablen an (siehe `inventory/host_vars/vmpsateam02-01` unter dem key `postgresql`).
Dies geht einfach mit dem Ansible-Modul `community.general.postgresql_user`.

Die Datenbanken sind ebenfalls in den `host_vars` dokumentiert, und werden mit dem Ansible-Modul `community.general.postgresql_db` angelegt.
Die `host_vars` und die `databases.yml`-Datei in der `postgresql`-Rolle bieten auch hier wieder eine gute Übersicht.
Das Ansible-Modul hilft uns, den jeweiligen Owner für die Datenbank inklusive encoding und lc_collate, lc_ctype Einstellungen vorzunehmen. 

Die Permissions erstellen wir in der `roles.yml` der Rolle.
Auch hier benutzen wir wieder die Variablen aus unseren `host_vars`:

```yaml
    - name: early_bird_user
      password: ...
      databases:
        - name: early_bird
          source_address: 127.0.0.1/32
          privileges: ALL
    - name: team02_user
      password: ...
      databases:
        - name: team02
          source_address: 192.168.2.2/32
          privileges: ALL
    - name: wikijs # TODO: remove
      password: ...
      databases:
        - name: wikijs
          source_address: 0.0.0.0/0
          privileges: ALL
    - name: synapse_user
      password: !vault |
        $ANSIBLE_VAULT;1.1;AES256
        32303239383638313333336139393637373564656165353437343633643065353965303164366133
        3437653064653366306234633033343530393831366138320a336135386664313033623030306465
        33656336653466353131323162653864373262343163633133656331313461393664363765383466
        6332313033303335380a336233316665386633353037623533363663306362366339383636616165
        3737
      databases:
        - name: synapse
          source_address: 192.168.1.0/24
          privileges: ALL
    - name: ro_user
      password: ...
      databases:
        - name: early_bird
          source_address: 127.0.0.1/32
          privileges: SELECT
        - name: team02
          source_address: 127.0.0.1/32
          privileges: SELECT
        - name: wikijs
          source_address: 127.0.0.1/32
          privileges: SELECT
        - name: synapse
          source_address: 127.0.0.1/32
          privileges: SELECT
```

An der jeweiligen `source_address` kann man sehen, wie wir konfiguriert haben, dass die jeweiligen Nutzer nur von den jeweils auf dem Arbeitsblatt geforderten Adressen sich verbinden können.
Der `databases`-Key eines jeden Users beschreibt die Rechte und die Source-Adresse, von der er sich auf die jeweilige DB verbinden darf.
Wir vergeben die Rollen wie in der `roles.yml` beschrieben, mit dem Ansible-Modul `community.general.postgresql_privs`.

Die beiden Datenbanken, die wir im Rahmen dieses Aufgabenblatts erstellen, sind `early_bird` und `team02`.
Wie man oben sieht, kann auf `early_bird` nur der `early_bird_user` von localhost aus zugegriffen werden.
Auf `team02` kann nur der `team02`-User zugreifen, und zwar nur von der anderem VM aus, also `192.168.2.2`. 
Beide haben jeweils Vollzugriff (`privileges: ALL`).

Der `ro_user` ist unser read-only User, der nur lesen kann - aber auf allen Datenbanken.
Siehe auch hier wieder die `roles.yml` für die Konfiguration.

Für die korrekte Authentifizierung müssen wir noch die `pg_hba.conf`-Datei anfassen (siehe Datei in der `postgresql`-Rolle):
```text
local	replication	all	peer
local	all	postgres	peer
local	all	all	peer
host	replication	all	127.0.0.1/32	scram-sha-256
host	replication	all	::1/128	scram-sha-256
host	all	all	127.0.0.1/32	scram-sha-256
host	all	all	::1/128	scram-sha-256
host    replication     {{ postgresql.replication_user.name }}         192.168.2.2/32        md5

{% for user in postgresql.users %}
{% for database in user.databases %}
host {{ database.name }} {{ user.name }} {{ database.source_address }} md5
{% endfor %}
{% endfor %}
```

In der `for`-Schleife unseres Templates konfigurieren wir die Authentifizierung mit Passwort (md5) unserer User,
sowie die jeweils erlaubte Datenbank und die Source-Adresse.

## Replikation und Backup

Für die Repliaktion halten wir uns grob an [dieses Tutorial](https://ibrahimhkoyuncu.medium.com/postgresql-high-availability-read-replica-methodology-streaming-replication-and-replica-75f9067326e5).

Wir bauen ein Master-Slave Setup, wobei `vmpsateam02-01` der Master ist, und `vmpsateam02-02` der Slave.
Hierfür erlauben wir die Replication für den Replication-User `repuser` in der oben gezeigten `pg_hba.conf` von unserer VM02 aus.

In der `replication.yml` steht, wie wir den replication User anlegen:
```yaml
- name: create replication user
  shell: "sudo -u postgres psql -c \"CREATE USER {{ postgresql.replication_user.name }} WITH REPLICATION ENCRYPTED PASSWORD '{{ postgresql.replication_user.password }}';\""
```

In der `postgresql.conf` müssen wir noch folgende Einstellungen treffen:
```text
wal_level = replica
max_wal_senders = 3
```

Und anschließend den `postgresql`-Service neustarten.

Auf dem Slave installieren wir ebenfalls, analog wie auf dem Master, Postgres, mittels der `postgres-slave`-Rolle.
Da die Postgres-Backup-Utility keine existierenden Dateien überschreibt, stoppen wir zunächst Postgres auf dem Slave, und benennen das Data Directory um:

```shell
mv /var/lib/postgresql/16/main /var/lib/postgresql/16/main_old
```

Dann lassen wir einmal manuell die Backup-Utility laufen:

```shell
sudo -u postgres pg_basebackup -h 192.168.2.1 -D /var/lib/postgresql/16/main -U repuser -v -P --wal-method=stream -R 
```

In der `postgresql.conf` des Slave sind folgende Einstellungen notwendig:
```text
hot_standby = on
primary_conninfo = 'host=192.168.2.1 port=5432 user=repuser password=[...]'
data_sync_retry = on
```

Dann starten wir den `postgresql`-Service wieder.
Wir verifizieren, dass die Replikation funktioniert, indem wir einfach Daten in eine Tabelle auf dem Master schreiben, und diese auf dem Slave genau so wieder finden.

Da wir nun einen Slave haben, der immer die aktuellen Daten hat, können wir Backups vom Slave aus erstellen.
Somit ist die Nutzung des Masters nicht beeinträchtigt, wenn wir teure Dumps erstellen.

Hierfür erstellen wir ein Skript `/usr/local/bin/postgres_dump.sh`, das einen vollständigen Dump der Datenbank mittels `pg_dumpall` macht.
Die Ausgabe (stderr und stdout) leiten wir um in eine Log-Datei.
Die Log- und Backup-Dateien landen in `/var/backups/postgres`.
Das Skript kann man in unserer `postgresql-slave` Ansible-Rolle einsehen.

Wir fügen es mit dem `cron`-Ansible Modul einem Cron-Job hinzu, der jede Nacht um 2 Uhr läuft (vgl. `backups.yml` in der Rolle):
```yaml
- name: Add cron job for postgres user to run backup daily at 2 AM
  cron:
      name: "PostgreSQL backup"
      user: postgres
      minute: "0"
      hour: "2"
      job: "/usr/local/bin/postgres_dump.sh > /dev/null 2>&1"
```

Nachdem wir das Skript einmal laufen lassen, können wir verifizieren, dass alles geklappt hat:
```shell
root@vmpsateam02-02:~# cat /var/backups/postgres/backup_log_2024-09-15_20-40-52.log
[2024-09-15_20-40-52] Starting backup...
[2024-09-15_20-40-52] Backup successfully created: /var/backups/postgres/backup_2024-09-15_20-40-52.sql
```
