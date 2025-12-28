from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QCheckBox, QTextEdit
import socket
import mariadb
import random

class InterfaceClientChoix(QWidget):
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

        # Section des routeurs avec cases à cocher
        self.text_routeurs_label = QLabel("Routeurs disponibles :")
        layout.addWidget(self.text_routeurs_label)

        # Créer un layout vertical pour afficher les cases à cocher des routeurs
        self.routeurs_checkbox_layout = QVBoxLayout()  # Contiendra toutes les cases à cocher des routeurs
        layout.addLayout(self.routeurs_checkbox_layout)  # Ajouter ce layout dans le layout principal

        # Section des clients disponibles
        self.text_clients_label = QLabel("Clients disponibles :")
        self.text_clients = QComboBox(self)
        self.text_clients.addItem("Sélectionner un client")  # Option par défaut
        layout.addWidget(self.text_clients_label)
        layout.addWidget(self.text_clients)

        # Section pour l'IP manuelle du destinataire
        self.ip_dest_label = QLabel("IP du client destinataire :")
        self.ip_dest_input = QLineEdit(self)
        layout.addWidget(self.ip_dest_label)
        layout.addWidget(self.ip_dest_input)

        self.message_label = QLabel("Message à envoyer :")
        self.message_input = QLineEdit(self)
        layout.addWidget(self.message_label)
        layout.addWidget(self.message_input)

        self.sauts_label = QLabel("Nombre de sauts :")
        self.sauts_spinner = QLineEdit(self)
        layout.addWidget(self.sauts_label)
        layout.addWidget(self.sauts_spinner)

        self.messages_reçus_label = QLabel("Messages reçus :")
        self.messages_reçus_text = QTextEdit(self)
        self.messages_reçus_text.setReadOnly(True)
        layout.addWidget(self.messages_reçus_label)
        layout.addWidget(self.messages_reçus_text)

        self.send_button = QPushButton("Envoyer Message", self)
        self.send_button.clicked.connect(self.on_send)
        layout.addWidget(self.send_button)

        self.reload_db_button = QPushButton("Recharger la DB", self)
        self.reload_db_button.clicked.connect(self.reload_db)
        layout.addWidget(self.reload_db_button)

        self.setLayout(layout)

        # Ajouter les routeurs et clients dans la vue
        self.load_routeurs_and_clients()

    def get_ip_client(self):
        """Récupère l'IP locale du client dans un réseau local."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connexion à un serveur externe (Google DNS)
        ip = s.getsockname()[0]  # Récupère l'IP locale
        s.close()
        return ip

    def load_routeurs_and_clients(self):
        """Charge les routeurs et les clients à partir du serveur Master"""
        try:
            # Connexion au serveur master pour obtenir l'IP de la base de données
            s = socket.socket()
            s.connect((self.ip_master, self.port_master))  # Connexion au serveur maître
            # Recevoir l'IP de la base de données
            self.db_ip = s.recv(1024).decode()
            print(f"IP de la base de données reçue : {self.db_ip}")

            # Récupérer les routeurs et clients depuis la base de données
            conn = mariadb.connect(
                host=self.db_ip,  # Utilisation de l'IP de la base de données
                user="toto",
                password="toto",
                database="table_routage"
            )
            cur = conn.cursor()

            # Récupérer les routeurs
            cur.execute("SELECT nom, adresse_ip, port FROM routeurs WHERE type='routeur'")
            routeurs = cur.fetchall()
            conn.close()

            # Supprimer les anciens widgets dans le layout des cases à cocher avant de les ajouter à nouveau
            for i in reversed(range(self.routeurs_checkbox_layout.count())):
                widget = self.routeurs_checkbox_layout.itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()

            # Ajouter chaque routeur avec sa case à cocher dans la vue
            for r in routeurs:
                routeur_checkbox = QCheckBox(f"{r[0]} - {r[1]}:{r[2]}", self)  # Créer la case à cocher
                self.routeurs_checkbox_layout.addWidget(routeur_checkbox)  # Ajouter la case à cocher au layout

            # Récupérer les clients disponibles
            conn = mariadb.connect(
                host=self.db_ip,  # Utilisation de l'IP de la base de données
                user="toto",
                password="toto",
                database="table_routage"
            )
            cur = conn.cursor()
            cur.execute("SELECT nom FROM routeurs WHERE type='client'")
            clients = cur.fetchall()
            conn.close()

            # Ajouter les clients au ComboBox
            self.text_clients.clear()
            self.text_clients.addItem("Sélectionner un client")
            for c in clients:
                self.text_clients.addItem(c[0])

            # Changer l'état de la connexion
            self.connexion_state_label.setText("État de la connexion au serveur master : Connecté")

        except mariadb.Error as e:
            print(f"Erreur DB (routeurs/clients) : {str(e)}")
            self.connexion_state_label.setText("État de la connexion au serveur master : Erreur de connexion")

    def on_send(self):
        """Envoyer un message au destinataire choisi"""
        dest_client = self.text_clients.currentText()
        manual_ip = self.ip_dest_input.text()  # IP du destinataire saisie manuellement
        message = self.message_input.text()
        nb_sauts = self.sauts_spinner.text()

        if dest_client == "Sélectionner un client" and not manual_ip:
            self.messages_reçus_text.append("Erreur: Veuillez sélectionner un client ou entrer une IP manuellement.")
            return

        if not message:
            self.messages_reçus_text.append("Erreur: Veuillez entrer un message.")
            return

        # Utiliser l'IP manuelle ou la sélection du client
        if manual_ip:
            dest_client = manual_ip

        # Vérifier le nombre de sauts
        try:
            nb_sauts = int(nb_sauts)
            if nb_sauts <= 0:
                self.messages_reçus_text.append("Erreur: Le nombre de sauts doit être un entier positif.")
                return
        except ValueError:
            self.messages_reçus_text.append("Erreur: Le nombre de sauts doit être un entier.")
            return

        # Sélectionner aléatoirement les routeurs en fonction du nombre de sauts
        selected_routeurs = []
        all_routeurs = [checkbox.text() for checkbox in self.routeurs_checkbox_layout.children() if isinstance(checkbox, QCheckBox)]

        # Si aucun routeur n'est sélectionné, choisir des routeurs aléatoires
        if not selected_routeurs:
            selected_routeurs = random.sample(all_routeurs, min(nb_sauts, len(all_routeurs)))

        if not selected_routeurs:
            self.messages_reçus_text.append("Erreur: Aucun routeur disponible pour les sauts.")
            return

        # Simuler l'envoi du message
        self.messages_reçus_text.append(f"Message envoyé à {dest_client}: {message} (Sauts: {nb_sauts}, Routeurs: {', '.join(selected_routeurs)})")

    def reload_db(self):
        """Recharger la base de données pour récupérer les derniers routeurs et clients"""
        self.load_routeurs_and_clients()

    def is_valid_ip(self, ip):
        """Vérifier si l'IP est valide"""
        try:
            socket.inet_aton(ip)  # Utilise inet_aton pour valider l'IP
            return True
        except socket.error:
            return False
