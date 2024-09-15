# Praktikum Systemadministration
 
## Dokumentation

- [Aufgabenblatt 2](docs/sheet_02/README.md)
- [Aufgabenblatt 3](docs/sheet_03/README.md)
- [Aufgabenblatt 4](docs/sheet_04/README.md)
- [Aufgabenblatt 5](docs/sheet_05/README.md)
- [Aufgabenblatt 6](docs/sheet_06/README.md)
- [Aufgabenblatt 7](docs/sheet_07/README.md)
- [Aufgabenblatt 8](docs/sheet_08/README.md)
- [Aufgabenblatt 9](docs/sheet_09/README.md)
- [Aufgabenblatt 10](docs/sheet_10/README.md)
- [Aufgabenblatt 11](docs/sheet_11/README.md)

## Konventionen

### Rollen

Die `main.yml` einer Ansible Rolle importiert lediglich Tasks aus dem gleichen Ordner.

### Deployment-Rollen

Der Name einer Deployment-Rolle hat immer den Prefix `deploy-`, gefolgt von der Domain des Deployments.
Damit ist die Domain gemeint, unter der das fertige Deployment nachher für Nutzer abrufbar ist.

Beispiel: `deploy-early-bird.psa.team02.cit.tum.de`

### Tags

In der main.yml einer Rolle vergeben wir für einen importierten Task die folgenden Tags: `<RollenName>` und `<RollenName>-<Importierter Task>`.

Beispiel:
  - `nginx`
  - `nginx-config`

**Ausnahme**:

In Deployment-Rollen reicht `deploy`, bzw. `deploy-<Importierter Task>`, da Deployments sowieso immer in eigenen Playbooks
sind, und es zu keinen Tag-Kollisionen kommen kann.

### Variablen

- Host-spezifische Variablen unter `host_vars`
- Gruppenspezifische Variablen unter `group_vars`
- Rollenspezifische Variablen unter `<Rolle>/defaults/main.yml`

Variablen sollten immer den Rollennamen als obersten Parent-Key haben.

Beispiel in den `host_vars`:
```yaml
iptables:
  outgoing_explicit_allow:
    - 131.159.0.0/16 # FMI
    - 192.168.2.0/24
```

Somit können wir die Variable `outgoing_explicit_allow` auf einen Blick der `iptables` Rolle zuordnen.

**Ausnahmen**:
- Rollen-übergreifende Variablen (z.B. Host- oder Gruppenvariablen) dürfen hier eine Ausnahme bilden,
sollten aber nicht häufig vorkommen.
Variablen, die sich offensichtlich auf den Host selbst, und auf keine spezifische Rolle beziehen
(auch, wenn sie in einer oder mehreren Rollen benutzt wird), dürfen auch eine Ausnahme bilden.
- Rollen-Variablen für Deployment-Rollen haben als Parent-Key immer `deploy`

### Vault

Für Daten, die wir nicht in Klartext in das Repository commiten wollen (z.B. Secrets), verwenden wir `ansible-vault`.
Beim Provisionieren / Deployment muss das Passwort für den Ansible Vault angegeben werden.
Wir verwenden das gleiche Vault Passwort für alle verschlüsselten Secrets im Repository.
Für angenehmere Deployments kann man eine `ansible/.vault-key` Datei mit dem Encryption Key als Inhalt anlegen,
und mit der `ansible-playbook` Option `--vault-password-file` angeben.
Diese Datei ist in der `.gitignore` vermerkt.

### Neuen Nutzer anlegen

`provision.yml` mit den jeweiligen Tags in dieser Reihenfolge ausführen:
- Tags: `raid-filesystem` (erzeugt `home`-directory)
- Tags: `users,ldap-users`

