import sys
import threading
from PyQt6.QtWidgets import QApplication, QMessageBox
from interface_master import InterfaceMaster
from serveur_master import master  # Assurez-vous que 'master' est bien importé depuis serveur_master.py
import socket

def is_valid_ip(ip):
    """Vérifie si l'IP est valide"""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def run_master_gui(db_ip, master_port):
    """Fonction pour lancer l'interface graphique et le serveur master en parallèle"""
    app = QApplication(sys.argv)

    # Créer l'interface graphique du serveur Master
    gui = InterfaceMaster(db_ip)
    gui.show()

    def start_server():
        """Démarre le serveur Master dans un thread séparé"""
        if not is_valid_ip(db_ip):
            QMessageBox.critical(gui, "Erreur", "L'IP de la base de données n'est pas valide.")
            return

        try:
            print("Démarrage du serveur master en arrière-plan...")
            t = threading.Thread(target=master, args=(db_ip, master_port), daemon=True)
            t.start()
            gui.signal_connexion.emit()  # Mettre à jour l'interface pour indiquer que le serveur est en cours d'exécution
        except Exception as e:
            QMessageBox.critical(gui, "Erreur", f"Erreur lors du démarrage du serveur : {e}")
            return

    gui.signal_connexion.connect(start_server)

    sys.exit(app.exec())  # Lancer l'interface graphique

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage : python main.py <DB_IP> <MASTER_PORT>")
        sys.exit(1)

    db_ip = sys.argv[1]  # IP de la base de données
    master_port = int(sys.argv[2])  # Port du serveur Master

    if not is_valid_ip(db_ip):
        print("Erreur: L'IP de la base de données n'est pas valide.")
        sys.exit(1)

    # Lancer l'interface graphique et le serveur master
    run_master_gui(db_ip, master_port)
