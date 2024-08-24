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
unter `/mnt/raid/<vm>/home.bak/` auf `vmpsateam02-01` sichern:

```bash
rsync -av /home/ /mnt/raid/<vm>/home.bak/
```
bzw.
```bash
TODO: rsync command für VM02
```

Analog für `/var/lib` und `/var/www`:
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

