# Aufgabenblatt 06

ℹ️ Unsere Dokumentation verweist häufig auf unser Ansible-Repository.
Daher empfiehlt es sich, die Dokumentation in unserem Repository zu lesen:
[https://github.com/robynkoelle/sysadmin-ansible](https://github.com/robynkoelle/sysadmin-ansible).

Zu unserem Wiki.js: [http://131.159.74.56:60204](http://131.159.74.56:60204)
Die Login-Credentials sind im PSA-Wiki unter `Team 02 - Aufgabenblatt 06`. 
Die Admin-Credentials sind auf `vmpsateam02-01` unter `/root`.

Wir entscheiden uns für [Wiki.js](https://js.wiki/) als unsere Web-Applikation.
Dafür installieren wir zunächst Docker mittels der `docker`-Rolle in unserem Repository.

## Docker installieren

Dependencies installieren:
```yaml
- name: Install dependencies
  apt:
    name:
      - ca-certificates
      - curl
    state: present
```

Repository zu den apt-Sources hinzufügen (analog wie bei Aufgabenblatt 05):
```yaml
- name: download official docker gpg key
  get_url:
    url: https://download.docker.com/linux/ubuntu/gpg
    dest: /etc/apt/keyrings/docker.asc
    mode: "0644"

- name: add docker repository to apt sources
  shell: echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list

- name: update apt cache
  apt:
    update_cache: yes
```

Docker installieren:
```yaml
- name: install docker packages
  apt:
    name:
      - docker-ce
      - docker-ce-cli
      - containerd.io
      - docker-buildx-plugin
      - docker-compose-plugin
    state: present
```

Anschließend müssen wir wegen unserer HTTP-Proxy noch folgende Änderung vornehmen, damit Docker diese respektiert:
```text
# https://docs.docker.com/config/daemon/systemd/#httphttps-proxy
# "If you're behind an HTTP or HTTPS proxy server, for example in corporate settings, the daemon proxy configurations
# must be specified in the systemd service file, not in the daemon.json file or using environment variables."

- name: ensure directory exists
  file:
    path: /etc/systemd/system/docker.service.d
    state: directory

- name: copy systemd file
  template:
    src: etc/systemd/system/docker.service.d/http-proxy.conf
    dest: /etc/systemd/system/docker.service.d/http-proxy.conf
  notify: restart docker
```

Die `http-proxy.conf` findet man in unserer `docker`-Rolle.

## Web-Applikation installieren

Mit der `deploy-wikijs.psa-team02.cit.tum.de`-Rolle deployen wir die Applikation.
Dies geht leicht mit dem `docker_container` Ansible-Modul:

```yaml
- name: add container
  community.docker.docker_container:
    name: wikijs
    image: ghcr.io/requarks/wiki:2
    ports:
      - 8081:3000
    env:
      DB_TYPE: postgres
      DB_HOST: 192.168.2.1
      DB_PORT: "5432"
      DB_USER: wikijs
      DB_PASS: "..."
      DB_NAME: wikijs
    restart: true
    restart_policy: unless-stopped
```

Die Applikation läuft im Container auf Port 3000, was wir auf Port 8081 unserer VM mappen.
Für Port 8081 haben wir eine Port-Weiterleitung mit der VirtualBox GUI eingerichtet, damit man unser Wiki.js mit der URL ganz oben in diesem Dokument aufrufen kann.

## Anbindung Team-Datenbanken

Wir haben von der Praktikumsleitung die Erlaubnis bekommen, sowohl für Team01 eine Datenbank zur Verfügung zu stellen,
als auch die Datenbank von Team01 zu konsumieren (anstatt jeweils verschiedener Teams).

In der Dokumentation für Aufgabenblatt 05 haben wir bereits beschrieben, wie wir Datenbanken und User anlegen.
Die DB und der User für Team01 existieren bei uns wie in den `inventory/host_vars/vmpsateam02-01` unter dem Key `postgresql` dokumentiert.
Wir haben ebenfalls unser Wiki.js-Deployment so konfiguriert, dass Wiki.js die Datenbank von Team 01 nutzt.
Wir haben es in beiden Richtungen getestet, und konnten verifizieren, dass unsere Web-Applikationen unter der Nutzung der DB des jeweils anderen Teams einwandfrei funktioniert.

Am Tag der Abgabe teilt Team01 uns leider mit, dass sie Probleme mit ihrer Firewall haben, die sie kurzfristig nicht mehr beheben können.
Deshalb können sie unsere Datenbank nicht nutzen (sie ist aber trotzdem weiterhin live und kann jederzeit genutzt werden).
Ihre Firewall-Regeln verbieten es uns nun auch, mit ihrer Datenbank zu kommunizieren.
Deshalb verwenden wir jetzt die bei uns selbst gehostete `wikijs`-Datenbank.

Relevante Commits:
- [Add database for team01](https://github.com/robynkoelle/sysadmin-ansible/commit/76e2a79f7b90cf871a84a4f1cc311d27a0d3468c)
- [Use team01 database for wikijs](https://github.com/robynkoelle/sysadmin-ansible/commit/953ceaceea04b2c507821508ce75c7b166cc010c)
- [Use team02 database for wikijs](https://github.com/robynkoelle/sysadmin-ansible/commit/ab27ee7651e2839387ec33595ab8c059c64155b6)

## Ersteinrichtung der Web-Applikation

Über die GUI legen wir im Browser den Admin-User für Wiki.js an.
Wie in unserer Präsentation demonstriert gibt es in Wiki.js die Möglichkeit, verschiedene User und Gruppen anzulegen.
Wir haben für jedes Team eine Gruppe angelegt, und für jeden Praktikumsteilnehmer einen Nutzer, der der jeweiligen Gruppe zugehört.
Wir haben außerdem (wie auch bereits in der Präsentation demonstriert) beispielhafte Seiten angelegt, die jeweils nur von bestimmten Nutzern bzw. Gruppen aufgerufen bzw. editiert werden können.
