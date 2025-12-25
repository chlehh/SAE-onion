import sys
from PyQt6.QtWidgets import QApplication
from interface_client import InterfaceClient

def main():
    app = QApplication(sys.argv)

    # Crée et affiche l'interface de connexion du client
    window = InterfaceClient()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()


