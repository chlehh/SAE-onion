from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QTextEdit
import socket
import mariadb

class InterfaceClient(QWidget):
    def __init__(self, ip_master, port_master, port_client, client_name):
        super().__init__()
        self.setWindowTitle("Client - Choisir un Destinataire et Envoyer un Message")
        self.setGeometry(200, 200, 600, 500)

        self.ip_master = ip_master
        self.port_master = port_master
        self.port_client = port_client
        self.client_name = client_name
        self.db_ip = None  # L'IP de la base de données sera reçue du serveur master

        # Layout principal pour la deuxième interface
        layout = QVBoxLayout()

        # Affichage des informations
        self.info_label = QLabel(f"Nom du client : {self.client_name}")
        layout.addWidget(self.info_label)

        self.ip_client_label = QLabel(f"IP du Client: {self.get_ip_client()}")
        layout.addWidget(self.ip_client_label)

        self.connexion_state_label = QLabel("État de la connexion au serveur master : Non connecté")
        layout.addWidget(self.connexion_state_label)

        # Section des clients disponibles
        self.text_clients_label = QLabel("Clients disponibles :")
        self.text_clients = QComboBox(self)
        self.text_clients.addItem("Sélectionner un client")  # Option par défaut
        layout.addWidget(self.text_clients_label)
        layout.addWidget(self.text_clients)

        self.message_label = QLabel("Message à envoyer :")
        self.message_input = QLineEdit(self)
        layout.addWidget(self.message_label)
        layout.addWidget(self.message_input)

        self.send_button = QPushButton("Envoyer Message", self)
        self.send_button.clicked.connect(self.on_send)
        layout.addWidget(self.send_button)

        self.setLayout(layout)

        # Ajouter les clients dans la vue
        self.load_clients_and_routeurs()

    def get_ip_client(self):
        """Récupère l'IP locale du client dans un réseau local."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connexion à un serveur externe (Google DNS)
        ip = s.getsockname()[0]  # Récupère l'IP locale
        s.close()
        return ip

    def load_clients_and_routeurs(self):
        """Récupérer la liste des clients et des routeurs depuis la base de données"""
        try:
            # Récupérer l'IP de la base de données du serveur master
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.ip_master, self.port_master))
            s.sendall("GET_DB_IP".encode())  # Demander l'IP de la base de données
            self.db_ip = s.recv(1024).decode()  # Recevoir l'IP de la base de données

            conn = mariadb.connect(
                host=self.db_ip,  # Utilisation de l'IP de la base de données
                user="toto",
                password="toto",
                database="table_routage"
            )
            cur = conn.cursor()

            # Récupérer les clients disponibles
            cur.execute("SELECT nom FROM routeurs WHERE type='client'")
            clients = cur.fetchall()

            # Récupérer les routeurs
            cur.execute("SELECT nom FROM routeurs WHERE type='routeur'")
            routeurs = cur.fetchall()
            conn.close()

            # Ajouter les clients au ComboBox
            self.text_clients.clear()
            self.text_clients.addItem("Sélectionner un client")
            for c in clients:
                self.text_clients.addItem(c[0])

            # Changer l'état de la connexion
            self.connexion_state_label.setText("État de la connexion au serveur master : Connecté")

        except mariadb.Error as e:
            print(f"Erreur DB (clients) : {str(e)}")
            self.connexion_state_label.setText("État de la connexion au serveur master : Erreur de connexion")

    def on_send(self):
        """Envoyer un message au destinataire choisi"""
        dest_client = self.text_clients.currentText()
        message = self.message_input.text()

        if dest_client == "Sélectionner un client":
            self.messages_reçus_text.append("Erreur: Veuillez sélectionner un client.")
            return

        if not message:
            self.messages_reçus_text.append("Erreur: Veuillez entrer un message.")
            return

        # Simuler l'envoi du message
        self.messages_reçus_text.append(f"Message envoyé à {dest_client}: {message}")
