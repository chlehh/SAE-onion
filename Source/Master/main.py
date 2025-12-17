import sys
import threading
from PyQt6.QtWidgets import QApplication
from interface_master import InterfaceMaster, InterfaceMasterConnexion
from serveur_master import master

def run_master_gui():
    app = QApplication(sys.argv)

    # Crée l'interface graphique pour se connecter au serveur Master
    gui = InterfaceMaster()
    gui.show()

    # Connexion à l'interface d'après la première interface pour afficher les informations
    def start_server(ip_db, port_master):
        # Démarre le serveur Master dans un thread séparé
        t = threading.Thread(target=master, args=(ip_db, port_master), daemon=True)
        t.start()

    gui.signal_connexion.connect(start_server)

    sys.exit(app.exec())

if __name__ == "__main__":
    run_master_gui()
