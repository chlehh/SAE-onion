#!/usr/bin/env python3
"""
client.py
Point d'entrée pour lancer le client avec son interface graphique
"""

import sys
from PyQt6.QtWidgets import QApplication
from interface_client import InterfaceClient

def main():
    if len(sys.argv) != 5:
        print("Usage incorrect!")
        print("Usage : python client.py <NOM> <PORT> <MASTER_IP> <MASTER_PORT>")
        print("Exemple : python client.py ClientA 7001 192.168.1.179 5000")
        sys.exit(1)
    
    nom = sys.argv[1]
    port = int(sys.argv[2])
    master_ip = sys.argv[3]
    master_port = int(sys.argv[4])
    
    print("="*60)
    print(f"LANCEMENT DU CLIENT {nom}")
    print("="*60)
    print(f"Port d'ecoute : {port}")
    print(f"Master : {master_ip}:{master_port}")
    print("="*60 + "\n")
    
    app = QApplication(sys.argv)
    window = InterfaceClient(nom, port, master_ip, master_port)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()