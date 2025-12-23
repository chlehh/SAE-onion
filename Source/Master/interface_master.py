from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton
from PyQt6.QtCore import pyqtSignal
import socket
import mariadb

class InterfaceMaster(QWidget):
    signal_connexion = pyqtSignal(str, int)  # Signal pour envoyer les infos de connexion vers la fonction master

    def __init__(self, db_ip):
        super().__init__()
        self.setWindowTitle("Serveur Master - Interface")
        self.setGeometry(200, 200, 600, 500)

        self.db_ip = db_ip  # Assigner l'IP de la base de données à un attribut de la classe

        # Layout principal pour l'interface
        layout = QVBoxLayout()

        # Affichage de l'IP du serveur Master
        self.ip_master_label = QLabel(f"IP du serveur Master : {self.get_ip_master()}")
        layout.addWidget(self.ip_master_label)

        # Affichage des routeurs connectés
        self.text_routeurs_label = QLabel("Routeurs connectés :")
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

        # Bouton pour actualiser la liste des routeurs et logs
        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.clicked.connect(self.load_routeurs)
        layout.addWidget(self.btn_refresh)

        # Définir le layout principal
        self.setLayout(layout)

        # Récupérer les routeurs depuis la base de données
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
            self.text_logs.append(f"Erreur DB (routeurs) : {str(e)}")

    def load_logs(self):
        """Charge et affiche les logs depuis la base de données"""
        try:
            # Récupérer les logs depuis la base de données
            conn = mariadb.connect(
                host=self.db_ip,  # Utilisation de l'IP de la base de données
                user="toto",
                password="toto",
                database="table_routage"
            )
            cur = conn.cursor()
            cur.execute("SELECT message_id, routeur, timestamp FROM logs ORDER BY timestamp DESC")
            logs = cur.fetchall()
            conn.close()

            # Afficher les logs dans le QTextEdit
            self.text_logs.clear()
            for log in logs:
                self.text_logs.append(f"{log[2]} - {log[1]} - {log[0]}")

        except Exception as e:
            self.text_logs.append(f"Erreur DB (logs) : {str(e)}")
