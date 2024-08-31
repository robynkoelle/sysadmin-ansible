# Aufgabenblatt 7: okumentation

## Festplatten anlegen

Team 01 stellt folgendes Skript zur Verfügung (danke), um die Festplatten und den SATA Controller über die Commandline anzulegen:
```bash
#!/bin/bash

vm_name=vmpsateam02-01
disk_size=2048

VBoxManage storagectl vmpsateam02-01 --name SATA --add sata --controller IntelAhci --portcount 30

for i in {0..6}; do
        file_name="/opt/psa/data/VirtualBox.users/$(whoami)/VirtualBox VMs/${vm_name}/fileserver-disk${i}.vmdk"
        VBoxManage createmedium --filename "${file_name}" --size ${disk_size} --format VMDK
        VBoxManage storageattach ${vm_name} --storagectl SATA --port ${i} --device 0 --type hdd --medium "${file_name}"
done
```
Wir erstellen insgesamt 7 Festplatten à 2048MB auf `vmpsateam02-01`.
Über die GUI haben wir verifiziert, dass die Platten erstellt und korrekt assoziiert wurden.

## RAID-Verbund anlegen
Wir entscheiden uns für einen RAID-5 Verbund mit 7 Festplatten.
Somit können 6 Platten für Datenspeicherung genutzt werden. 

Wir nutzen hierfür mdadm (siehe in der `raid`-Rolle):
```bash
mdadm --create --level={{ raid.level }} '{{ raid.device }}' --raid-devices={{ raid.devices_count }} {{ raid.devices }}
```

Anschließend müssen wir noch das neu angelegte device mounten.
Mit den Ansible-Modulen `ansible.community.filesystem` und `ansible.posix.mount` erzeugen wir jeweils ein ext4-Dateisystem,
und mounten es (inklusive `fstab`-Eintrag).

Mit `df -h` verifizieren wir, dass der Mountpoint existiert, und die gewünschte Mindestgröße hat:

```bash
/dev/md0         12G   24K   12G   1% /mnt/raid
```

## Daten migrieren

Wir migrieren die Home-Verzeichnisse der Nutzer, indem wir zunächst die bestehenden Daten (auf allen unseren VMs)
unter `/mnt/raid/<vm>/home.bak/` auf `vmpsateam02-01` mit `rsync` sichern, beispielsweise mit diesem Command auf `vmpsateam02-01`:

```bash
rsync -a /home/ /mnt/raid/<vm>/home.bak/
```

Die Daten von `vmpsateam02-02` wurden ebenfalls manuell zu `vmpsateam02-01` kopiert (via `rsync`).

Analog für `/var/lib` und `/var/www` (und auch für `vmpsateam02-02`):
```bash
rsync -a --relative /var/lib /mnt/raid/vmpsateam02-01
rsync -a --relative /var/www /mnt/raid/vmpsateam02-01
...
```

Auf `vmpsateam02-01` können wir direkt die Mounts erstellen (siehe [mounts/create.yml](../../ansible/roles/mounts/tasks/create.yml)):
```yml
mounts:
    - to: /var/lib
      from: /mnt/raid/vmpsateam02-01/var/lib
    - to: /var/www
      from: /mnt/raid/vmpsateam02-01/var/www
    - to: /home.bak
      from: /mnt/raid/vmpsateam02-01/home.bak
```

Um die analogen Mounts für `vmpsateam02-02` zu erstellen, müssen wir zunächst den NFS-Server auf `vmpsateam02-01` einrichten.

## NFS-Server einrichten 

Wir installieren `nfs-kernel-server` via `apt`, und definieren die exports wie in [/etc/exports](../../ansible/roles/raid/templates/vmpsateam02-01/etc/exports) beschrieben.

Der Server muss über den `systemd`-Service neugestartet werden, nachdem die in der Konfigurationsdatei referenzierten Pfade angelegt wurden (da er sie vorher logischerweise nicht gefunden hat).

Damit die anderen VMs auf NFS zugreifen können, konfigurieren wir noch fixe Ports in [/etc/nfs.conf](../../ansible/roles/raid/templates/vmpsateam02-01/etc/nfs.conf), und die nötigen `iptables`-Regeln auf `vmpsateam02-01`:

```
# Incoming nfs
{% for network in networks.teams %}
-A INPUT -p tcp --dport {{ nfs.port }} -s {{ network }} -j ACCEPT
-A INPUT -p udp --dport {{ nfs.port }} -s {{ network }} -j ACCEPT
-A INPUT -p tcp --dport {{ nfs.rpcbind_port }} -s {{ network }} -j ACCEPT
-A INPUT -p udp --dport {{ nfs.rpcbind_port }} -s {{ network }} -j ACCEPT
-A INPUT -p tcp --dport {{ nfs.mountd_port }} -s {{ network }} -j ACCEPT
-A INPUT -p udp --dport {{ nfs.mountd_port }} -s {{ network }} -j ACCEPT
-A INPUT -p tcp --dport {{ nfs.statd_port }} -s {{ network }} -j ACCEPT
-A INPUT -p udp --dport {{ nfs.statd_port }} -s {{ network }} -j ACCEPT
-A INPUT -p tcp --dport {{ nfs.lockd_tcpport }} -s {{ network }} -j ACCEPT
-A INPUT -p udp --dport {{ nfs.lockd_udpport }} -s {{ network }} -j ACCEPT
{% endfor %}
```

## autofs konfigurieren

Nun können wir auf `vmpsateam02-02` via `autofs` die analogen Mounts konfigurieren.
Die config templates `auto.home`, `auto.var`, und `auto.master` in der [autofs-Rolle](../../ansible/roles/autofs) ermöglichen dies.

Nach einem restart des `autofs`-Services konnten wir verifizieren, dass `vmpsateam02-02` in `/home.bak` schreiben kann,
und die geschriebenen Daten unter `/mnt/raid/vmpsateam02-02/home.bak` auf `vmpsateam02-01` auftauchen.
Lesen funktioniert auch, und beides auch in die andere Richtung.

Analog wurde nach manuellem `rsync` noch mittels `autofs` jeweils `/var/lib` und `/var/www` von `vmpsateam02-02`
auf `/mnt/raid/vmpsateam02-02/var/(lib|www)` gemountet.

Notiz: `fstab` mountet die directories beim Boot - daher war nach der `autofs`-Konfiguration ein Reboot nötig.

## Samba konfigurieren

Wir installieren samba mit apt:
```shell
apt install samba
```

Wir konfigurieren Samba mit der [smb.conf](../../roles/samba/templates/vmpsateam02-01/etc/smb.conf).
Hierbei haben wir für die home-Verzeichnisse (also unter `"[homes]"`) folgende Einstellungen getroffen:
- browsable = no, damit die Freigaben der anderen User nicht öffentlich gelistet werden können
- read only = no, damit geschrieben werden kann
- create mask = 0700, damit nur der Eigentümer seine eigenen Daten schreiben / lesen kann.
- directory mask analog
- `valid users: %S`, damit nur der gerade angemeldete User in sein Verzeichnis schreiben kann.

Wir legen außerdem die Samba-User mittels `sambapasswd` an, wie in der [`samba`-Rolle](../../ansible/roles/samba) beschrieben.
Jeder User hat dabei von uns ein Passwort vergeben bekommen.
Die Passwörter haben wir mittels `ansible-vault` verschlüsselt, um sie in diesem Repository verwalten zu können.

In `iptables` geben wir für Samba die Ports `139` und `445` frei (wie schon häufig beschrieben).

Wir verifizieren die Funktionalität von Samba wie folgt:
`smbclient //localhost/<username> -U <username>`
Hierfür mussten wir den smbclient (mittels `apt`) auf unseren VMs installieren.

Dann konnten wir innerhalb einer interaktiven Shell erfolgreich Daten in dem jeweiligen Home-Verzeichnis anlegen / ändern / löschen.

