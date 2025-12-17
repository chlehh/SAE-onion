from PyQt6.QtCore import pyqtSignal  # Ajoutez cette ligne pour importer pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit
import socket

class InterfaceMaster(QWidget):
    signal_connexion = pyqtSignal(str, int)  # Signal pour envoyer les infos de connexion vers la fonction master

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serveur Master")
        self.setGeometry(200, 200, 600, 400)

        # Layout principal pour l'interface
        layout = QVBoxLayout()

        # Barre en rouge pour afficher l'IP du serveur Master
        self.barre_ip = QLineEdit(self)
        self.barre_ip.setText(self.get_ip_locale())  # Récupère l'IP de la machine locale
        self.barre_ip.setStyleSheet("background-color: red; color: white;")
        self.barre_ip.setReadOnly(True)  # L'IP est automatiquement affichée mais non modifiable ici
        layout.addWidget(self.barre_ip)

        # Entrée pour l'IP de la base de données et port du serveur Master
        self.ip_db_label = QLabel("IP de la base de données:")
        self.ip_db_input = QLineEdit(self)

        self.port_master_label = QLabel("Port du serveur Master:")
        self.port_master_input = QLineEdit(self)

        self.bouton_connexion = QPushButton("Démarrer le Serveur Master", self)
        self.bouton_connexion.clicked.connect(self.on_connexion)

        layout.addWidget(self.ip_db_label)
        layout.addWidget(self.ip_db_input)
        layout.addWidget(self.port_master_label)
        layout.addWidget(self.port_master_input)
        layout.addWidget(self.bouton_connexion)

        self.setLayout(layout)

    def get_ip_locale(self):
        """Récupère l'IP locale de la machine"""
        return socket.gethostbyname(socket.gethostname())

    def on_connexion(self):
        """Lorsqu'on appuie sur 'Démarrer le Serveur Master', émettre les informations de connexion."""
        ip_db = self.ip_db_input.text()  # IP de la base de données
        port_master = int(self.port_master_input.text())  # Port du serveur Master
        self.signal_connexion.emit(ip_db, port_master)


class InterfaceMasterConnexion(QWidget):
    def __init__(self, ip_db, port_master):
        super().__init__()
        self.setWindowTitle("Serveur Master - Connexion")
        self.setGeometry(200, 200, 600, 400)

        # Layout principal pour la deuxième interface
        layout = QVBoxLayout()

        self.text_routeurs_label = QLabel("Routeurs disponibles :")
        self.text_routeurs = QTextEdit(self)
        self.text_routeurs.setReadOnly(True)

        # Affichage des routeurs
        self.text_routeurs.setText("Routeur1 - 192.168.1.1:6001\nRouteur2 - 192.168.1.2:6002\nRouteur3 - 192.168.1.3:6003")

        self.setLayout(layout)

        self.load_routeurs()

    def load_routeurs(self):
        """Charge et affiche les routeurs depuis la base de données"""
        # Pour simplifier, ajoutons des routeurs fictifs
        self.text_routeurs.append("Routeur1 - 192.168.1.1:6001")
        self.text_routeurs.append("Routeur2 - 192.168.1.2:6002")
        self.text_routeurs.append("Routeur3 - 192.168.1.3:6003")
        self.text_routeurs.append("Routeur4 - 192.168.1.4:6004")
