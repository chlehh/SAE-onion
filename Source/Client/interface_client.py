from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal
from interface_client_choix import InterfaceClientChoix  # Importer correctement la classe

class InterfaceClient(QWidget):
    signal_connexion = pyqtSignal(str, int, int)  # Signal pour envoyer les infos de connexion vers la deuxième interface

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Client - Connexion au Serveur Master")
        self.setGeometry(200, 200, 400, 300)

        # Layout principal pour la connexion
        layout = QVBoxLayout()

        self.ip_master_label = QLabel("IP du Serveur Master:")
        self.ip_master_input = QLineEdit(self)

        self.port_master_label = QLabel("Port du Serveur Master:")
        self.port_master_input = QLineEdit(self)

        self.port_client_label = QLabel("Port du Client:")
        self.port_client_input = QLineEdit(self)

        self.bouton_connexion = QPushButton("Se connecter", self)
        self.bouton_connexion.clicked.connect(self.on_connexion)

        layout.addWidget(self.ip_master_label)
        layout.addWidget(self.ip_master_input)
        layout.addWidget(self.port_master_label)
        layout.addWidget(self.port_master_input)
        layout.addWidget(self.port_client_label)
        layout.addWidget(self.port_client_input)
        layout.addWidget(self.bouton_connexion)

        self.setLayout(layout)

    def on_connexion(self):
        """Lorsqu'on appuie sur 'Se connecter', émettre les informations de connexion."""
        ip_master = self.ip_master_input.text()
        port_master = int(self.port_master_input.text())
        port_client = int(self.port_client_input.text())
        self.signal_connexion.emit(ip_master, port_master, port_client)
        self.ouvrir_deuxieme_interface(ip_master, port_master, port_client)

    def ouvrir_deuxieme_interface(self, ip_master, port_master, port_client):
        """Ouvre la deuxième interface une fois la connexion établie."""
        self.deuxieme_interface = InterfaceClientChoix(ip_master, port_master, port_client)
        self.deuxieme_interface.show()
        self.close()
