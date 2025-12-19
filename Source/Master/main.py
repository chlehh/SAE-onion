import sys
import threading
from PyQt6.QtWidgets import QApplication
from interface_master import InterfaceMaster  # Interface pour la connexion au Master
from serveur_master import master  # Fonction pour démarrer le serveur Master
import time

def run_master_gui(db_ip, master_port):
    app = QApplication(sys.argv)

    # Créer l'interface graphique du serveur Master
    gui = InterfaceMaster(db_ip)  # Passer l'IP de la base de données à l'interface
    gui.show()

    # Fonction pour démarrer le serveur Master dans un thread séparé
    def start_server():
        # Démarre le serveur Master dans un thread séparé
        t = threading.Thread(target=master, args=(db_ip, master_port), daemon=True)
        t.start()
        
        # Attendre quelques secondes pour s'assurer que le serveur Master est prêt
        time.sleep(2)  # Attendre 2 secondes (ajustez si nécessaire)

    # Connexion du bouton de l'interface à la fonction qui lance le serveur
    gui.signal_connexion.connect(start_server)

    sys.exit(app.exec())

if __name__ == "__main__":
    # Vérifiez si les arguments nécessaires ont été passés
    if len(sys.argv) != 3:
        print("Usage: python main.py <DB_IP> <MASTER_PORT>")
        sys.exit(1)

    # Récupérer l'IP de la base de données et le port du serveur Master depuis les arguments de ligne de commande
    db_ip = sys.argv[1]  # L'IP de la base de données
    master_port = int(sys.argv[2])  # Le port du serveur Master

    # Lancer l'interface graphique avec les informations de connexion
    run_master_gui(db_ip, master_port)
