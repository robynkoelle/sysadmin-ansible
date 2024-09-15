# Aufgabenblatt 11

ℹ️ Unsere Dokumentation verweist häufig auf unser Ansible-Repository.
Daher empfiehlt es sich, die Dokumentation in unserem Repository zu lesen:
[https://github.com/robynkoelle/sysadmin-ansible](https://github.com/robynkoelle/sysadmin-ansible).

## John the Ripper
Zuerst überprüfen wir, ob sichere Passwörter für die User gesetzt wurden. Dabei verwenden wir das Tool `john` um die Hashes in LDAP zu cracken.
Mit `slapcat` dumpen wir unser LDAP in eine Datei, danach filtern wir die BASE64 kodierten hashes heraus und dekodieren diese. Damit haben wir eine Liste von Hashes, welche so aussieht:
```
{SSHA}AFFEEC0FFEE==
```
Da es praktisch nicht möglich ist alle Passwörter zu probiere, verwenden wir die bewährte wordlist `rockyou.txt` um die Passwörter zu cracken. Mit folgendem Befehl setzen wir john für die Passwörter ein:
```
john --wordlist=rockyou.txt ldap.hash
```
Nach sehr kurzer Zeit terminiert `john` und wenn es Passwörter gefunden hat, kann man diese mit folgendem Befehe anzeigen:
```
john --show ldap.hash
```
Allerdings waren die Passwörter so sicher, dass wir keine Passwörter cracken konnten. Natürlich könnte man größere wordlists verwenden oder mit Hashcat und GPUs die Passwörter schneller cracken, aber wir gehen hierbei davon aus, dass die Passwörter sicher genug sind.


## DNS Amplification Attack
In den Aufgabenblättern wurde nichts dazu erwähnt, dass wir DNS Amplification Attacken verhindern sollen. Deswegen war es naheliegend auf diese zu testen.
Mit dem Metasploit framework und `scanner/dns/dns_am` können wir das gesamte Praktikumsnetzwerk scannen und herausfinden, ob DNS Amplification Attacken möglich sind. Dabei erhalten wir folgende Ausgabe, welche vulnerable Hosts anzeigt:
```
[+] 192.168.1.2:53 - Response is 541 bytes [8.07x Amplification]
[+] 192.168.7.2:53 - Response is 548 bytes [8.18x Amplification]
[+] 192.168.2.1:53 - Response is 487 bytes [7.27x Amplification]
[+] 192.168.2.3:53 - Response is 487 bytes [7.27x Amplification]
[+] 192.168.8.1:53 - Response is 487 bytes [7.27x Amplification]
[+] 192.168.6.1:53 - Response is 487 bytes [7.27x Amplification]
[+] 192.168.5.2:53 - Response is 548 bytes [8.18x Amplification]
[*] 192.168.5.11:53 - Recursion not allowed
[*] 192.168.5.22:53 - Recursion not allowed
[+] 192.168.10.2:53 - Response is 487 bytes [7.27x Amplification]
[*] 192.168.9.1:53 - Recursion not allowed
[+] 192.168.3.1:53 - Response is 487 bytes [7.27x Amplification]
```
Dass ein Server betroffen ist, liegt daran, dass recursion erlaubt ist. Um zu verhindern, dass andere unseren Server für Amplifications verwenden, aber trotzdem recursion für uns selber erlauben, können wir `allow-recursion` einstellen. Dazu fügen wir folgende Zeilen in die `named.conf.options` hinzu:
```
allow-recursion { 
    192.168.2.0/24;
    127.0.0.0/8;
    10.0.0.0/8; 
};
```
Damit ist es zwar immer noch mögich, dass unser Subnets Opfer der Attacke wird, aber zumindest keine anderen mehr.

## Rootkit Detection

Mit dem Package `rkhunter` können wir Rootkits auf unseren Servern erkennen. Dazu installieren wir rkhunter mit apt, updaten und initialisieren die Datenbank mit `rkhunter --update` und `rkhunter --propupd` und führen es mit `rkhunter --check` aus. Dabei werden einige Warnungen ausgegeben, die aber auf false positives zurückzuführen sind, da SSH Root Login erlaubt sein soll. Außerdem wurden Postgres Datein unter /dev als verdächtig markiert.

## Port Scanning
Mit nmap können wir uns und andere Hosts im Netzwerk scannen. Dabei verwenden wir für unsere Server folgenden Befehl:
```bash
nmap -p- 192.168.2.1
```
Dabei fallen keine Ports auf, die nicht offen sein sollten. 

Allerdings können wir auch andere Hosts scannen, um zu überprüfen, ob diese sicher sind.
```bash
nmap --script vuln 192.168.0.0/24
```
Da es zu lange dauert das komplette Subnet zu scannen, haben wir ein paar zufällige IPs gescannt. Dabei haben wir keine offensichtlichen Schwachstellen gefunden.

## Auf anderen Hosts
Wir suchen auf anderen VMs nach zu offenen File Permissions, da diese für privilege escalation genutzt werden können. Dazu verwenden wir folgenden Befehl:
```bash
find / -path /proc -prune -o -type f -perm /o=w -print
```
Dies wurde auf mehreren VMs der anderen Teams durchgeführt, jedoch wurden keine offenen File Permissions gefunden.

## Intrusion Detection
Zur frühen Erkennung von Angriffen setzen wir `AIDE - Advanced Intrusion Detection Environment` ein. Dabei wird ein Hash von allen Dateien erstellt und in einer Datenbank gespeichert. Wenn sich Dateien ändern, wird dies erkannt und eine Warnung ausgegeben. Dazu installieren wir AIDE mit apt und initialisieren es mit `aideinit`.

Um die Installation zu verfizieren kann man mit `aide -c aide.conf --check` die veränderten Datein sehen.