import sys
from PyQt6.QtWidgets import QApplication
from interface_master import InterfaceMaster  # Importer l'interface pour la première connexion

def run_master_gui():
    app = QApplication(sys.argv)

    # Crée l'interface graphique pour se connecter au serveur Master
    gui = InterfaceMaster()
    gui.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    run_master_gui()
