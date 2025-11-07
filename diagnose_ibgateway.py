#!/usr/bin/env python3
"""
Diagnostic avancé IB Gateway
"""
import socket
import subprocess
import sys
import time
from pathlib import Path

def check_process(name):
    """Vérifie si un processus est en cours d'exécution"""
    try:
        result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {name}', '/NH'],
                              capture_output=True, text=True, shell=True)
        return name in result.stdout
    except:
        return False

def check_port(host, port):
    """Vérifie si un port est ouvert"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def main():
    print("=" * 60)
    print("🔍 Diagnostic IB Gateway")
    print("=" * 60)
    print()

    # 1. Vérification des processus
    print("📋 [1] Vérification des processus...")
    processes_to_check = ['java.exe', 'javaw.exe', 'ibgateway.exe', 'ibgateway1.exe']

    found_processes = []
    for proc in processes_to_check:
        if check_process(proc):
            found_processes.append(proc)
            print(f"   ✅ {proc} trouvé")
        else:
            print(f"   ❌ {proc} non trouvé")

    if not found_processes:
        print("   ⚠️  Aucun processus IB Gateway détecté")
    else:
        print(f"   📊 {len(found_processes)} processus trouvés")

    print()

    # 2. Vérification des ports
    print("🌐 [2] Vérification des ports...")

    ports_to_check = [
        ('127.0.0.1', 4002, 'IB Gateway'),
        ('127.0.0.1', 7497, 'TWS Live'),
        ('127.0.0.1', 7496, 'TWS Paper')
    ]

    open_ports = []
    for host, port, service in ports_to_check:
        if check_port(host, port):
            open_ports.append((host, port, service))
            print(f"   ✅ Port {port} ({service}) ouvert")
        else:
            print(f"   ❌ Port {port} ({service}) fermé")

    if not open_ports:
        print("   ⚠️  Aucun port IBKR ouvert")
    else:
        print(f"   📊 {len(open_ports)} ports ouverts")

    print()

    # 3. Chemins d'installation
    print("📁 [3] Chemins d'installation...")

    paths_to_check = [
        r'C:\Jts\ibgateway\1037\ibgateway.exe',
        r'C:\Jts\ibgateway\latest\ibgateway.exe',
        r'C:\IB Gateway\ibgateway.exe'
    ]

    found_paths = []
    for path in paths_to_check:
        if Path(path).exists():
            found_paths.append(path)
            print(f"   ✅ {path}")
        else:
            print(f"   ❌ {path}")

    if not found_paths:
        print("   ⚠️  Aucun chemin d'installation trouvé")
    else:
        print(f"   📊 {len(found_paths)} chemins trouvés")

    print()

    # 4. Test de connexion Python
    print("🐍 [4] Test de connexion Python...")

    try:
        from ib_insync import IB
        print("   ✅ ib_insync installé")

        # Test rapide de connexion
        ib = IB()
        try:
            # Essayer de se connecter avec un timeout court
            ib.connect('127.0.0.1', 4002, clientId=99, timeout=2)
            print("   ✅ Connexion IB Gateway réussie")
            ib.disconnect()
        except Exception as e:
            print(f"   ❌ Connexion IB Gateway échouée: {str(e)[:50]}...")

        try:
            ib.connect('127.0.0.1', 7497, clientId=99, timeout=2)
            print("   ✅ Connexion TWS réussie")
            ib.disconnect()
        except Exception as e:
            print(f"   ❌ Connexion TWS échouée: {str(e)[:50]}...")

    except ImportError:
        print("   ❌ ib_insync non installé")

    print()

    # 5. Recommandations
    print("💡 [5] Recommandations...")

    if not found_processes and not open_ports:
        print("   🚨 IB Gateway ne semble pas être lancé")
        print("   📋 Actions recommandées:")
        print("      1. Lancez IB Gateway manuellement")
        print("      2. Vérifiez que vous êtes connecté")
        print("      3. Assurez-vous que l'API est activée")
    elif found_processes and not open_ports:
        print("   ⚠️  Processus trouvé mais ports fermés")
        print("   📋 Vérifiez la configuration API dans IB Gateway")
    elif not found_processes and open_ports:
        print("   ❓ Ports ouverts mais pas de processus - vérifiez")
    else:
        print("   ✅ Configuration semble correcte")

    print()
    print("=" * 60)

if __name__ == "__main__":
    main()