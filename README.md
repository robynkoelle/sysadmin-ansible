# Praktikum Systemadministration
 
## Dokumentation

- [Aufgabenblatt 2](docs%2Fsheet_02%2FREADME.md)
- [Aufgabenblatt 3](docs%2Fsheet_03%2FREADME.md)
- [Aufgabenblatt 4](docs%2Fsheet_04%2FREADME.md)

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
