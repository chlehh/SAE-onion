import sys
from PyQt6.QtWidgets import QApplication
from interface_client import InterfaceClient
from cryptographie import generer_cle_rsa

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
    print(f"Port d'écoute : {port}")
    print(f"Master : {master_ip}:{master_port}")
    print("="*60 + "\n")
    
    # Générer les clés publiques et privées pour le chiffrement RSA
    pub_key, priv_key = generer_cle_rsa()
    
    app = QApplication(sys.argv)
    window = InterfaceClient(nom, port, master_ip, master_port, pub_key, priv_key)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
