from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QCheckBox, QPushButton, QLineEdit, QSpinBox, QComboBox
import socket
import mariadb

class InterfaceClientChoix(QWidget):
    def __init__(self, ip_master, port_master, port_client):
        super().__init__()
        self.setWindowTitle("Client - Sélectionner les routeurs et le message")
        self.setGeometry(200, 200, 600, 500)

        self.ip_master = ip_master
        self.port_master = port_master
        self.port_client = port_client
        self.db_ip = None  # L'IP de la base de données sera reçue du serveur master

        # Récupérer l'IP du client
        self.client_ip = self.get_ip_client()

        # Layout principal pour la deuxième interface
        layout = QVBoxLayout()

        # Afficher l'IP du client
        self.ip_client_label = QLabel(f"IP du Client: {self.client_ip}")
        layout.addWidget(self.ip_client_label)

        # Affichage de l'état de la connexion au serveur master
        self.connexion_state_label = QLabel("État de la connexion au serveur master : Non connecté")
        layout.addWidget(self.connexion_state_label)

        # Afficher les routeurs disponibles
        self.text_routeurs_label = QLabel("Routeurs disponibles :")
        self.text_routeurs = QTextEdit(self)
        self.text_routeurs.setReadOnly(True)
        layout.addWidget(self.text_routeurs_label)
        layout.addWidget(self.text_routeurs)

        # Afficher les clients disponibles
        self.text_clients_label = QLabel("Clients disponibles :")
        self.text_clients = QComboBox(self)
        self.text_clients.addItem("Sélectionner un client")  # Option par défaut
        layout.addWidget(self.text_clients_label)
        layout.addWidget(self.text_clients)

        # Sélection des routeurs
        self.routeur_selection_label = QLabel("Sélectionnez les routeurs :")
        self.routeurs_checkbox = []

        # Ajouter une zone pour l'IP du deuxième client
        self.ip_client_label = QLabel("IP du deuxième client :")
        self.ip_client_input = QLineEdit(self)
        layout.addWidget(self.ip_client_label)
        layout.addWidget(self.ip_client_input)

        # Ajouter un champ pour saisir le message à envoyer
        self.message_label = QLabel("Message à envoyer :")
        self.message_input = QLineEdit(self)
        layout.addWidget(self.message_label)
        layout.addWidget(self.message_input)

        # Champ pour saisir le nombre de sauts
        self.sauts_label = QLabel("Nombre de sauts :")
        self.sauts_spinner = QSpinBox(self)
        self.sauts_spinner.setMinimum(1)
        self.sauts_spinner.setMaximum(10)
        layout.addWidget(self.sauts_label)
        layout.addWidget(self.sauts_spinner)

        # Section pour les messages reçus
        self.messages_reçus_label = QLabel("Messages reçus :")
        self.messages_reçus_text = QTextEdit(self)
        self.messages_reçus_text.setReadOnly(True)
        layout.addWidget(self.messages_reçus_label)
        layout.addWidget(self.messages_reçus_text)

        # Bouton d'envoi
        self.send_button = QPushButton("Envoyer Message", self)
        self.send_button.clicked.connect(self.on_send)
        layout.addWidget(self.send_button)

        # Bouton pour recharger la base de données
        self.reload_db_button = QPushButton("Recharger la DB", self)
        self.reload_db_button.clicked.connect(self.reload_db)
        layout.addWidget(self.reload_db_button)

        self.setLayout(layout)

        # Récupérer l'IP de la base de données et les routeurs et clients depuis le serveur master
        self.load_routeurs_and_clients()

    def get_ip_client(self):
        """Récupère l'IP locale du client dans un réseau local."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connexion à un serveur externe (Google DNS)
        ip = s.getsockname()[0]  # Récupère l'IP locale
        s.close()
        print(f"Adresse IP récupérée : {ip}")
        return ip

    def load_routeurs_and_clients(self):
        """Charge les routeurs et les clients à partir du serveur Master"""
        try:
            # Connexion au serveur master pour obtenir l'IP de la base de données
            s = socket.socket()
            s.connect((self.ip_master, self.port_master))
            # Recevoir l'IP de la base de données
            self.db_ip = s.recv(1024).decode()
            print(f"IP de la base de données reçue : {self.db_ip}")

            # Maintenant récupérer les routeurs et clients depuis la base de données
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

            # Afficher les routeurs dans le QTextEdit
            self.text_routeurs.clear()
            for r in routeurs:
                self.text_routeurs.append(f"{r[0]} - {r[1]}:{r[2]}")

            # Créer dynamiquement des cases à cocher pour chaque routeur
            for r in routeurs:
                routeur_checkbox = QCheckBox(r[0], self)
                self.routeurs_checkbox.append(routeur_checkbox)
                self.layout().addWidget(routeur_checkbox)

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

    def reload_db(self):
        """Recharger la base de données pour récupérer les derniers routeurs disponibles"""
        self.load_routeurs_and_clients()

    def on_send(self):
        """Lorsqu'on appuie sur 'Envoyer Message', on envoie les informations au Master"""
        selected_routeurs = [checkbox.text() for checkbox in self.routeurs_checkbox if checkbox.isChecked()]
        ip_client = self.ip_client_input.text()
        message = self.message_input.text()
        nb_sauts = self.sauts_spinner.value()

        if nb_sauts > len(selected_routeurs):
            self.show_error_message(f"Erreur : Vous avez sélectionné {nb_sauts} sauts, mais il n'y a que {len(selected_routeurs)} routeurs disponibles.")
            return

        self.send_message(selected_routeurs, ip_client, message, nb_sauts)

    def send_message(self, routeurs_choisis, ip_client, message, nb_sauts):
        """Envoie le message au serveur Master avec les paramètres sélectionnés"""
        print(f"Routeurs sélectionnés : {routeurs_choisis}")
        print(f"IP du client à contacter : {ip_client}")
        print(f"Message à envoyer : {message}")
        print(f"Nombre de sauts sélectionnés : {nb_sauts}")

        # Construire le message en oignon
        onion_message = self.construire_oignon(routeurs_choisis, message)
        print(f"Oignon construit : {onion_message}")

        # Simuler l'envoi du message au premier routeur
        premier_routeur = routeurs_choisis[0]  # Prendre le premier routeur sélectionné
        ip, port = self.get_routeur_ip_and_port(premier_routeur)
        self.envoyer_message(ip, port, onion_message)

    def construire_oignon(self, chemin, message_final):
        """Construit un message en oignon avec les informations de chaque routeur"""
        msg = f"{message_final}"

        # On remonte le chemin à l'envers pour créer les couches
        for routeur in reversed(chemin):
            msg = f"{routeur}|{msg}"

        return msg

    def get_routeur_ip_and_port(self, routeur):
        """Récupère l'IP et le port du routeur"""
        ROUTEURS = {
        }
        return ROUTEURS.get(routeur, ("", 0))

    def envoyer_message(self, ip, port, message):
        """Envoie le message au routeur ou client suivant"""
        s = socket.socket()
        s.connect((ip, port))
        s.send(message.encode())
        s.close()

    def show_error_message(self, message):
        """Affiche un message d'erreur dans la section 'Messages reçus'"""
        self.messages_reçus_text.append(f"ERREUR: {message}")

    def add_received_message(self, message):
        """Affiche un message reçu dans la section 'Messages reçus'"""
        self.messages_reçus_text.append(f"Message reçu: {message}")
