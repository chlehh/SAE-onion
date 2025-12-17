from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QCheckBox, QPushButton, QLineEdit, QSpinBox
import socket

class InterfaceClientChoix(QWidget):
    def __init__(self, ip_master, port_master, port_client):
        super().__init__()
        self.setWindowTitle("Client - Sélectionner les routeurs et le message")
        self.setGeometry(200, 200, 600, 500)

        self.ip_master = ip_master
        self.port_master = port_master
        self.port_client = port_client

        # Récupérer l'IP du client
        self.client_ip = self.get_ip_client()

        # Layout principal pour la deuxième interface
        layout = QVBoxLayout()

        # Afficher l'IP du client
        self.ip_client_label = QLabel(f"IP du Client: {self.client_ip}")
        layout.addWidget(self.ip_client_label)

        # Afficher les routeurs disponibles
        self.text_routeurs_label = QLabel("Routeurs disponibles :")
        self.text_routeurs = QTextEdit(self)
        self.text_routeurs.setReadOnly(True)
        layout.addWidget(self.text_routeurs_label)
        layout.addWidget(self.text_routeurs)

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

        self.setLayout(layout)

        self.load_routeurs()

    def get_ip_client(self):
        """Récupère l'IP locale du client"""
        return socket.gethostbyname(socket.gethostname())

    def load_routeurs(self):
        """Charge les routeurs à partir du serveur Master"""
        # Pour simplifier, ajoutons des routeurs fictifs
        self.text_routeurs.setText("Routeur1 - 192.168.1.1:6001\nRouteur2 - 192.168.1.2:6002\nRouteur3 - 192.168.1.3:6003")

        # Créer dynamiquement des cases à cocher pour chaque routeur
        routeurs = ["Routeur1", "Routeur2", "Routeur3"]
        for routeur in routeurs:
            routeur_checkbox = QCheckBox(routeur, self)
            self.routeurs_checkbox.append(routeur_checkbox)
            self.layout().addWidget(routeur_checkbox)

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

        # Simuler l'envoi du message en oignon
        chemin = self.demander_chemin_au_master(nb_sauts)
        print(f"Chemin sélectionné par le client : {chemin}")

        # Construire le message en oignon
        onion_message = self.construire_oignon(routeurs_choisis, message)
        print(f"Oignon construit : {onion_message}")

        # Simuler l'envoi du message au premier routeur
        premier_routeur = routeurs_choisis[0]  # Prendre le premier routeur sélectionné
        ip, port = self.get_routeur_ip_and_port(premier_routeur)
        self.envoyer_message(ip, port, onion_message)

    def demander_chemin_au_master(self, nb_sauts):
        """Demande un chemin au serveur Master"""
        # Pour simuler la demande de chemin au serveur Master
        return ["Routeur1", "Routeur2", "Routeur3"][:nb_sauts]

    def construire_oignon(self, chemin, message_final):
        """Construit un message en oignon avec les informations de chaque routeur"""
        msg = f"{message_final}"

        # On remonte le chemin à l'envers pour créer les couches
        for routeur in reversed(chemin):
            msg = f"{routeur}|{msg}"

        return msg

    def get_routeur_ip_and_port(self, routeur):
        """Récupère l'IP et le port du routeur"""
        # Pour simplifier, nous retournons des informations fictives
        ROUTEURS = {
            "Routeur1": ("192.168.1.1", 6001),
            "Routeur2": ("192.168.1.2", 6002),
            "Routeur3": ("192.168.1.3", 6003)
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
