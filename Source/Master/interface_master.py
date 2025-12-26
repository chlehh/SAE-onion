from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QLineEdit, QTabWidget, QHBoxLayout, QFormLayout
import socket
import mariadb

class InterfaceMaster(QWidget):
    signal_connexion = pyqtSignal()  # Signal pour démarrer le serveur master

    def __init__(self, db_ip):
        super().__init__()
        self.setWindowTitle("Serveur Master - Interface")
        self.setGeometry(200, 200, 600, 500)

        self.db_ip = db_ip  # Assigner l'IP de la base de données à un attribut de la classe

        # Layout principal pour l'interface
        layout = QVBoxLayout()

        # Création du QTabWidget pour gérer les onglets
        self.tab_widget = QTabWidget(self)
        layout.addWidget(self.tab_widget)

        # Onglet 1: Détails du serveur et logs
        self.page_1 = QWidget()
        self.page_1_layout = QVBoxLayout()

        self.ip_master_label = QLabel(f"IP du serveur Master : {self.get_ip_master()}")
        self.ip_master_port_label = QLabel(f"Port du serveur Master : 5001")
        self.page_1_layout.addWidget(self.ip_master_label)
        self.page_1_layout.addWidget(self.ip_master_port_label)

        self.text_routeurs_label = QLabel("Routeurs connectés :")
        self.text_routeurs = QTextEdit(self)
        self.text_routeurs.setReadOnly(True)
        self.page_1_layout.addWidget(self.text_routeurs_label)
        self.page_1_layout.addWidget(self.text_routeurs)

        self.text_logs_label = QLabel("Logs :")
        self.text_logs = QTextEdit(self)
        self.text_logs.setReadOnly(True)
        self.page_1_layout.addWidget(self.text_logs_label)
        self.page_1_layout.addWidget(self.text_logs)

        # Bouton pour passer à l'onglet de gestion des clients et routeurs
        self.btn_goto_page_2 = QPushButton("Gestion des clients et routeurs", self)
        self.btn_goto_page_2.clicked.connect(self.goto_page_2)
        self.page_1_layout.addWidget(self.btn_goto_page_2)

        self.page_1.setLayout(self.page_1_layout)

        # Onglet 2: Gestion des clients et routeurs
        self.page_2 = QWidget()
        self.page_2_layout = QVBoxLayout()

        # Section pour ajouter un client
        self.add_client_label = QLabel("Ajouter un client :")
        self.client_name_input = QLineEdit(self)
        self.add_client_button = QPushButton("Ajouter Client")
        self.add_client_button.clicked.connect(self.add_client)

        # Section pour ajouter un routeur
        self.add_router_label = QLabel("Ajouter un routeur :")
        self.router_name_input = QLineEdit(self)
        self.add_router_button = QPushButton("Ajouter Routeur")
        self.add_router_button.clicked.connect(self.add_router)

        # Section pour supprimer un routeur
        self.delete_router_label = QLabel("Supprimer un routeur :")
        self.router_name_delete_input = QLineEdit(self)
        self.delete_router_button = QPushButton("Supprimer Routeur")
        self.delete_router_button.clicked.connect(self.delete_router)

        # Section pour supprimer un client
        self.delete_client_label = QLabel("Supprimer un client :")
        self.client_name_delete_input = QLineEdit(self)
        self.delete_client_button = QPushButton("Supprimer Client")
        self.delete_client_button.clicked.connect(self.delete_client)

        # Ajouter les champs et boutons de gestion des clients et routeurs
        self.page_2_layout.addWidget(self.add_client_label)
        self.page_2_layout.addWidget(self.client_name_input)
        self.page_2_layout.addWidget(self.add_client_button)
        self.page_2_layout.addWidget(self.add_router_label)
        self.page_2_layout.addWidget(self.router_name_input)
        self.page_2_layout.addWidget(self.add_router_button)
        self.page_2_layout.addWidget(self.delete_router_label)
        self.page_2_layout.addWidget(self.router_name_delete_input)
        self.page_2_layout.addWidget(self.delete_router_button)
        self.page_2_layout.addWidget(self.delete_client_label)
        self.page_2_layout.addWidget(self.client_name_delete_input)
        self.page_2_layout.addWidget(self.delete_client_button)

        self.page_2.setLayout(self.page_2_layout)

        # Ajouter les deux pages au QTabWidget (onglets)
        self.tab_widget.addTab(self.page_1, "Serveur et Logs")
        self.tab_widget.addTab(self.page_2, "Gestion Clients et Routeurs")

        # Charger les routeurs depuis la base de données
        self.load_routeurs()

    def get_ip_master(self):
        """Retourne l'IP locale de la machine"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connecte à un serveur pour obtenir l'IP locale
        ip = s.getsockname()[0]
        s.close()
        return ip

    def load_routeurs(self):
        """Charge et affiche les routeurs depuis la base de données"""
        try:
            # Récupérer les informations depuis la base de données (DB)
            conn = mariadb.connect(
                host=self.db_ip,  # Utilisation de l'IP de la base de données
                user="toto",
                password="toto",
                database="table_routage"
            )
            cur = conn.cursor()
            cur.execute("SELECT nom, adresse_ip, port FROM routeurs WHERE type='routeur'")
            routeurs = cur.fetchall()
            conn.close()

            # Afficher les routeurs dans le QTextEdit
            self.text_routeurs.clear()
            for r in routeurs:
                self.text_routeurs.append(f"{r[0]} - {r[1]}:{r[2]}")

            # Enregistrer un log indiquant que les routeurs ont été actualisés
            self.text_logs.append("Routeurs actualisés.")

        except Exception as e:
            self.text_logs.append(f"Erreur DB (routeurs) : {e}")

    def add_client(self):
        """Ajouter un client à la base de données"""
        client_name = self.client_name_input.text()
        if client_name:
            try:
                conn = mariadb.connect(
                    host=self.db_ip,
                    user="toto",
                    password="toto",
                    database="table_routage"
                )
                cur = conn.cursor()
                cur.execute("INSERT INTO routeurs (nom, type) VALUES (%s, 'client')", (client_name,))
                conn.commit()
                conn.close()
                self.text_logs.append(f"Client {client_name} ajouté.")
                self.load_routeurs()  # Rafraîchir la liste des routeurs
            except mariadb.Error as e:
                self.text_logs.append(f"Erreur DB : {e}")
        else:
            self.text_logs.append("Nom du client vide.")

    def add_router(self):
        """Ajouter un routeur à la base de données"""
        router_name = self.router_name_input.text()
        if router_name:
            try:
                conn = mariadb.connect(
                    host=self.db_ip,
                    user="toto",
                    password="toto",
                    database="table_routage"
                )
                cur = conn.cursor()
                cur.execute("INSERT INTO routeurs (nom, type) VALUES (%s, 'routeur')", (router_name,))
                conn.commit()
                conn.close()
                self.text_logs.append(f"Routeur {router_name} ajouté.")
                self.load_routeurs()  # Rafraîchir la liste des routeurs
            except mariadb.Error as e:
                self.text_logs.append(f"Erreur DB : {e}")
        else:
            self.text_logs.append("Nom du routeur vide.")

    def delete_router(self):
        """Supprimer un routeur de la base de données"""
        router_name = self.router_name_delete_input.text()
        if router_name:
            try:
                conn = mariadb.connect(
                    host=self.db_ip,
                    user="toto",
                    password="toto",
                    database="table_routage"
                )
                cur = conn.cursor()
                cur.execute("DELETE FROM routeurs WHERE nom = %s", (router_name,))
                conn.commit()
                conn.close()
                self.text_logs.append(f"Routeur {router_name} supprimé.")
                self.load_routeurs()  # Rafraîchir la liste des routeurs
            except mariadb.Error as e:
                self.text_logs.append(f"Erreur DB : {e}")
        else:
            self.text_logs.append("Nom du routeur vide.")

    def delete_client(self):
        """Supprimer un client de la base de données"""
        client_name = self.client_name_delete_input.text()
        if client_name:
            try:
                conn = mariadb.connect(
                    host=self.db_ip,
                    user="toto",
                    password="toto",
                    database="table_routage"
                )
                cur = conn.cursor()
                cur.execute("DELETE FROM routeurs WHERE nom = %s AND type = 'client'", (client_name,))
                conn.commit()
                conn.close()
                self.text_logs.append(f"Client {client_name} supprimé.")
                self.load_routeurs()  # Rafraîchir la liste des routeurs
            except mariadb.Error as e:
                self.text_logs.append(f"Erreur DB : {e}")
        else:
            self.text_logs.append("Nom du client vide.")

    def goto_page_2(self):
        """Changer pour la page 2 (gestion des clients/routeurs)"""
        self.tab_widget.setCurrentIndex(1)
