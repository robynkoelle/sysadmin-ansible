#!/bin/bash

# Function to check RAID status
check_raid_status() {
    echo "Test 1: Überprüfung des RAID-Status"
    
    # Filter out the correct line for the overall RAID state
    raid_status=$(sudo mdadm --detail /dev/md0 | grep -E "^\s+State\s+:" | awk '{print $3}')
    
    if [ "$raid_status" == "clean" ]; then
        echo "RAID-Status: OK (State: clean)"
    else
        echo "RAID-Status: WARNING (State: $raid_status)"
    fi
}


# Function to check filesystem usage
check_filesystem() {
    echo "Test 2: Überprüfung des Dateisystems"
    df_output=$(df -h /mnt/raid | awk 'NR==2 {print $5}')
    usage=$(echo "$df_output" | sed 's/%//')
    echo "Dateisystem Auslastung: $df_output"
    if [ "$usage" -gt 90 ]; then
        echo "WARNING: Dateisystem ist über 90% voll!"
    fi
}

# Function to check NFS shares
check_nfs_shares() {
    echo "Test 3: Überprüfung der NFS-Freigaben"
    nfs_shares=$(showmount -e localhost | grep '/mnt/raid')
    if [ -z "$nfs_shares" ]; then
        echo "WARNING: Keine NFS-Freigaben gefunden!"
    else
        echo "NFS-Freigaben: OK"
        echo "$nfs_shares"
    fi
}

# Function to check Samba configuration
check_samba_config() {
    echo "Test 4: Überprüfung der Samba-Konfiguration"
    smb_status=$(smbclient -L localhost -U% -m SMB3 2>/dev/null | grep -i "Sharename")
    if [ -z "$smb_status" ]; then
        echo "WARNING: Samba-Konfiguration konnte nicht abgerufen werden!"
    else
        echo "Samba-Konfiguration: OK"
    fi
}

# Function to check iptables rules for NFS and Samba
check_iptables_rules() {
    echo "Test 5: Überprüfung der relevanten iptables-Regeln"

    echo "NFS-Regeln:"
    nfs_rules=$(sudo iptables -L -v -n | grep -E '2049|111')
    if [ -z "$nfs_rules" ]; then
        echo "WARNING: Keine NFS-Regeln in iptables gefunden!"
    else
        echo "NFS-Regeln: OK"
        echo "$nfs_rules"
    fi

    echo "Samba-Regeln:"
    samba_rules=$(sudo iptables -L -v -n | grep -E '137|138|139|445')
    if [ -z "$samba_rules" ]; then
        echo "WARNING: Keine Samba-Regeln in iptables gefunden!"
    else
        echo "Samba-Regeln: OK"
        echo "$samba_rules"
    fi
}

# Function to check home directory mount status
check_home_mount_status() {
    echo "Test 6: Überprüfung des Mount-Status der Home-Verzeichnisse"
    home_mounts=$(mount | grep autofs)
    if [ -z "$home_mounts" ]; then
        echo "WARNING: Home-Verzeichnisse nicht gemountet!"
    else
        echo "Mount-Status: OK"
        echo "$home_mounts"
    fi
}

# Run all checks
check_raid_status
check_filesystem
check_nfs_shares
check_samba_config
check_iptables_rules
check_home_mount_status

echo "Alle Tests abgeschlossen."
