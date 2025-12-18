import mariadb
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton

class InterfaceMasterConnexion(QWidget):
    def __init__(self, ip_db, port_master):
        super().__init__()
        self.setWindowTitle("Serveur Master - Connexion")
        self.setGeometry(200, 200, 600, 400)

        self.ip_db = ip_db
        self.port_master = port_master

        # Layout principal pour la deuxième interface
        layout = QVBoxLayout()

        # Affichage des routeurs disponibles
        self.text_routeurs_label = QLabel("Routeurs disponibles :")
        self.text_routeurs = QTextEdit(self)
        self.text_routeurs.setReadOnly(True)
        layout.addWidget(self.text_routeurs_label)
        layout.addWidget(self.text_routeurs)

        # Affichage des logs
        self.text_logs_label = QLabel("Logs :")
        self.text_logs = QTextEdit(self)
        self.text_logs.setReadOnly(True)
        layout.addWidget(self.text_logs_label)
        layout.addWidget(self.text_logs)

        # Bouton pour actualiser la liste des routeurs
        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.clicked.connect(self.load_routeurs)
        layout.addWidget(self.btn_refresh)

        # Affichage de l'IP des clients
        self.text_clients_label = QLabel("Clients disponibles :")
        self.text_clients = QTextEdit(self)
        self.text_clients.setReadOnly(True)
        layout.addWidget(self.text_clients_label)
        layout.addWidget(self.text_clients)

        self.setLayout(layout)

        # Charger les routeurs et clients depuis la base de données
        self.load_routeurs()

    def load_routeurs(self):
        """Charge et affiche les routeurs depuis la base de données"""
        try:
            conn = mariadb.connect(
                host=self.ip_db,
                user="toto",
                password="toto",
                database="table_routage"
            )
            cur = conn.cursor()
            cur.execute("SELECT nom, adresse_ip, port FROM routeurs WHERE type='routeur'")
            routeurs = cur.fetchall()
            conn.close()

            self.text_routeurs.clear()
            for r in routeurs:
                self.text_routeurs.append(f"{r[0]} - {r[1]}:{r[2]}")

            self.text_logs.append("Routeurs actualisés.")

            # Afficher les clients disponibles
            self.load_clients()

        except Exception as e:
            self.text_logs.append(f"Erreur DB : {str(e)}")

    def load_clients(self):
        """Charge et affiche les clients depuis la base de données"""
        try:
            conn = mariadb.connect(
                host=self.ip_db,
                user="toto",
                password="toto",
                database="table_routage"
            )
            cur = conn.cursor()
            cur.execute("SELECT nom, adresse_ip FROM routeurs WHERE type='client'")
            clients = cur.fetchall()
            conn.close()

            self.text_clients.clear()
            for client in clients:
                self.text_clients.append(f"{client[0]} - {client[1]}")

        except Exception as e:
            self.text_logs.append(f"Erreur DB (clients) : {str(e)}")
