#!/usr/bin/env python3
"""
main.py
Lance le serveur Master avec son interface graphique
"""

import sys
import threading
import time
from PyQt6.QtWidgets import QApplication
from interface_master import InterfaceMaster
from serveur_master import master, monitor_routeurs, get_db_connection

def run_master_gui(db_ip, master_port):
    """Fonction pour lancer l'interface graphique et le serveur master en parallèle"""
    
    # Tester la connexion à la base de données AVANT de tout lancer
    print(" Test de connexion à la base de données...")
    test_conn = get_db_connection(db_ip)
    if test_conn:
        print(" Connexion à la base de données réussie\n")
        test_conn.close()
    else:
        print(" Impossible de se connecter à la base de données")
        print("Vérifiez l'IP de la base de données et les identifiants")
        sys.exit(1)
    
    print("="*60)
    print("  SERVEUR MASTER - ROUTAGE EN OIGNON")
    print("="*60)
    print(f" Base de données : {db_ip}")
    print(f" Port d'écoute : {master_port}")
    print("="*60 + "\n")
    
    # Démarrer le serveur Master dans un thread séparé AVANT l'interface
    print(" Démarrage du serveur master en arrière-plan...")
    server_thread = threading.Thread(
        target=master, 
        args=(db_ip, master_port), 
        daemon=True
    )
    server_thread.start()
    print(" Serveur master démarré\n")
    
    # Démarrer la surveillance des routeurs dans un thread séparé
    print(" Démarrage de la surveillance des routeurs...")
    monitor_thread = threading.Thread(
        target=monitor_routeurs, 
        args=(db_ip, 60), 
        daemon=True
    )
    monitor_thread.start()
    print(" Surveillance des routeurs activée (vérification toutes les 60s)\n")
    
    # Attendre un peu pour s'assurer que le serveur a démarré
    time.sleep(1)
    
    # Créer et lancer l'interface graphique
    print(" Lancement de l'interface graphique...\n")
    app = QApplication(sys.argv)
    gui = InterfaceMaster(db_ip, master_port)
    gui.show()
    
    print("="*60)
    print(" Système complet lancé avec succès!")
    print("="*60 + "\n")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(" Usage incorrect!")
        print("Usage : python main.py <DB_IP> <MASTER_PORT>")
        print("Exemple : python main.py 192.168.1.179 5000")
        sys.exit(1)

    db_ip = sys.argv[1]
    master_port = int(sys.argv[2])

    # Lancer l'interface graphique et le serveur master
    run_master_gui(db_ip, master_port)