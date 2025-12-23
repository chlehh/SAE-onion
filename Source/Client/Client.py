import sys
from PyQt6.QtWidgets import QApplication
from interface_client import InterfaceClient
from interface_client_choix import InterfaceClientChoix

def run_client_gui():
    app = QApplication(sys.argv)

    # Créer l'interface graphique pour se connecter au serveur Master
    gui = InterfaceClient()
    gui.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    run_client_gui()
