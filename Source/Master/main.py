#!/usr/bin/env python3
"""Lance le serveur Master avec son interface graphique"""

import sys
import threading
import time
from PyQt6.QtWidgets import QApplication
from interface_master import InterfaceMaster
from serveur_master import master, monitor_routeurs, get_db_connection

def run_master_gui(db_ip, master_port):
    """Lance le Master avec GUI"""
    
    print("Test connexion DB...")
    test_conn = get_db_connection(db_ip)
    if test_conn:
        print("Connexion DB OK\n")
        test_conn.close()
    else:
        print("Impossible de se connecter a la DB")
        sys.exit(1)
    
    print("="*60)
    print("  SERVEUR MASTER - ROUTAGE EN OIGNON")
    print("="*60)
    print(f"Base de donnees : {db_ip}")
    print(f"Port d'ecoute : {master_port}")
    print("="*60 + "\n")
    
    print("Demarrage du serveur master...")
    server_thread = threading.Thread(
        target=master,
        args=(db_ip, master_port),
        daemon=True
    )
    server_thread.start()
    print("Serveur master demarre\n")
    
    print("Demarrage du monitoring...")
    monitor_thread = threading.Thread(
        target=monitor_routeurs,
        args=(db_ip, 60),
        daemon=True
    )
    monitor_thread.start()
    print("Monitoring actif (60s)\n")
    
    time.sleep(1)
    
    print("Lancement interface graphique...\n")
    app = QApplication(sys.argv)
    gui = InterfaceMaster(db_ip, master_port)
    gui.show()
    
    print("="*60)
    print("Systeme complet lance!")
    print("="*60 + "\n")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage incorrect!")
        print("Usage : python main.py <DB_IP> <MASTER_PORT>")
        print("Exemple : python main.py 192.168.1.179 5000")
        sys.exit(1)
    
    db_ip = sys.argv[1]
    master_port = int(sys.argv[2])
    
    run_master_gui(db_ip, master_port)