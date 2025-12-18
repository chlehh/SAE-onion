import sys
import socket
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal
from interface_master_connexion import InterfaceMasterConnexion  # Ajoutez cette ligne pour l'importation

class InterfaceMaster(QWidget):
    signal_connexion = pyqtSignal(str, int)  # Signal pour envoyer les infos de connexion vers la deuxième interface

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serveur Master - Connexion")
        self.setGeometry(200, 200, 600, 400)

        # Layout principal pour l'interface
        layout = QVBoxLayout()

        # Barre en rouge pour afficher l'IP du serveur Master
        self.barre_ip = QLineEdit(self)
        self.barre_ip.setText(self.get_ip_master())  # Récupère l'IP de la machine locale (Master)
        self.barre_ip.setStyleSheet("background-color: red; color: white;")
        self.barre_ip.setReadOnly(True)  # L'IP est automatiquement affichée mais non modifiable ici
        layout.addWidget(self.barre_ip)

        # Entrée pour l'IP de la base de données et port du serveur Master
        self.ip_db_label = QLabel("IP de la base de données:")
        self.ip_db_input = QLineEdit(self)

        self.port_master_label = QLabel("Port du serveur Master:")
        self.port_master_input = QLineEdit(self)

        self.bouton_connexion = QPushButton("Se connecter", self)
        self.bouton_connexion.clicked.connect(self.on_connexion)

        layout.addWidget(self.ip_db_label)
        layout.addWidget(self.ip_db_input)
        layout.addWidget(self.port_master_label)
        layout.addWidget(self.port_master_input)
        layout.addWidget(self.bouton_connexion)

        self.setLayout(layout)

    def get_ip_master(self):
        """Récupère l'IP locale de la machine"""
        return socket.gethostbyname(socket.gethostname())  # IP de la machine locale (Master)

    def on_connexion(self):
        """Lorsqu'on appuie sur 'Se connecter', émettre les informations de connexion."""
        ip_db = self.ip_db_input.text()  # IP de la base de données
        port_master = int(self.port_master_input.text())  # Port du serveur Master
        self.signal_connexion.emit(ip_db, port_master)
        self.ouvrir_deuxieme_interface(ip_db, port_master)

    def ouvrir_deuxieme_interface(self, ip_db, port_master):
        """Ouvre la deuxième interface une fois la connexion établie."""
        self.deuxieme_interface = InterfaceMasterConnexion(ip_db, port_master)
        self.deuxieme_interface.show()
        self.close()
