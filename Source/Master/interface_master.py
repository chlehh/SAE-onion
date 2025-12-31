#!/usr/bin/env python3
"""Interface graphique pour le serveur Master avec gestion"""

import sys
import mariadb
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QTableWidget, QTableWidgetItem, QTabWidget, 
                             QGroupBox, QMessageBox, QLineEdit, QComboBox)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont

class InterfaceMaster(QMainWindow):
    def __init__(self, db_ip, master_port):
        super().__init__()
        self.db_ip = db_ip
        self.master_port = master_port
        
        self.setWindowTitle(f"Serveur Master - Port {master_port}")
        self.setGeometry(100, 100, 1200, 800)
        
        self.init_ui()
        
        # Timer pour rafraîchir les données toutes les 5 secondes
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(5000)
        
        # Charger les données initiales
        self.refresh_data()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # En-tête
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Serveur Master - Routage en Oignon")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        info_label = QLabel(f"DB: {self.db_ip} | Port: {self.master_port}")
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(info_label)
        
        main_layout.addLayout(header_layout)
        
        # Statistiques
        stats_group = QGroupBox("Statistiques")
        stats_layout = QHBoxLayout()
        
        self.label_nb_routeurs = QLabel("Routeurs: 0")
        self.label_nb_routeurs.setStyleSheet("font-size: 14px; padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
        stats_layout.addWidget(self.label_nb_routeurs)
        
        self.label_nb_clients = QLabel("Clients: 0")
        self.label_nb_clients.setStyleSheet("font-size: 14px; padding: 10px; background-color: #f3e5f5; border-radius: 5px;")
        stats_layout.addWidget(self.label_nb_clients)
        
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        # Onglets
        tabs = QTabWidget()
        
        # ========== ONGLET ROUTEURS ==========
        tab_routeurs = QWidget()
        layout_routeurs = QVBoxLayout()
        
        self.table_routeurs = QTableWidget()
        self.table_routeurs.setColumnCount(5)
        self.table_routeurs.setHorizontalHeaderLabels(["Nom", "IP", "Port", "Cle Publique", "Actions"])
        self.table_routeurs.setColumnWidth(0, 150)
        self.table_routeurs.setColumnWidth(1, 150)
        self.table_routeurs.setColumnWidth(2, 100)
        self.table_routeurs.setColumnWidth(3, 300)
        self.table_routeurs.setColumnWidth(4, 100)
        
        layout_routeurs.addWidget(QLabel("Routeurs Enregistres"))
        layout_routeurs.addWidget(self.table_routeurs)
        
        btn_refresh_routeurs = QPushButton("Rafraichir")
        btn_refresh_routeurs.clicked.connect(self.refresh_data)
        layout_routeurs.addWidget(btn_refresh_routeurs)
        
        tab_routeurs.setLayout(layout_routeurs)
        tabs.addTab(tab_routeurs, "Routeurs")
        
        # ========== ONGLET CLIENTS ==========
        tab_clients = QWidget()
        layout_clients = QVBoxLayout()
        
        self.table_clients = QTableWidget()
        self.table_clients.setColumnCount(4)
        self.table_clients.setHorizontalHeaderLabels(["Nom", "IP", "Port", "Actions"])
        self.table_clients.setColumnWidth(0, 200)
        self.table_clients.setColumnWidth(1, 200)
        self.table_clients.setColumnWidth(2, 150)
        self.table_clients.setColumnWidth(3, 100)
        
        layout_clients.addWidget(QLabel("Clients Connectes"))
        layout_clients.addWidget(self.table_clients)
        
        btn_refresh_clients = QPushButton("Rafraichir")
        btn_refresh_clients.clicked.connect(self.refresh_data)
        layout_clients.addWidget(btn_refresh_clients)
        
        tab_clients.setLayout(layout_clients)
        tabs.addTab(tab_clients, "Clients")
        
        # ========== ONGLET GÉRER (3ème position) ==========
        tab_gerer = QWidget()
        layout_gerer = QVBoxLayout()
        
        # Section Lancer un Routeur
        group_routeur = QGroupBox("Lancer un Routeur")
        layout_form_routeur = QVBoxLayout()
        
        # Nom du routeur
        layout_nom_r = QHBoxLayout()
        layout_nom_r.addWidget(QLabel("Nom du routeur:"))
        self.input_nom_routeur = QLineEdit()
        self.input_nom_routeur.setPlaceholderText("Ex: R1")
        layout_nom_r.addWidget(self.input_nom_routeur)
        layout_form_routeur.addLayout(layout_nom_r)
        
        # Port du routeur
        layout_port_r = QHBoxLayout()
        layout_port_r.addWidget(QLabel("Port:"))
        self.input_port_routeur = QLineEdit()
        self.input_port_routeur.setPlaceholderText("Ex: 6001")
        layout_port_r.addWidget(self.input_port_routeur)
        layout_form_routeur.addLayout(layout_port_r)
        
        # Bouton lancer routeur
        btn_lancer_routeur = QPushButton("Lancer le Routeur")
        btn_lancer_routeur.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        btn_lancer_routeur.clicked.connect(self.lancer_routeur)
        layout_form_routeur.addWidget(btn_lancer_routeur)
        
        group_routeur.setLayout(layout_form_routeur)
        layout_gerer.addWidget(group_routeur)
        
        # Section Lancer un Client
        group_client = QGroupBox("Lancer un Client")
        layout_form_client = QVBoxLayout()
        
        # Nom du client
        layout_nom_c = QHBoxLayout()
        layout_nom_c.addWidget(QLabel("Nom du client:"))
        self.input_nom_client = QLineEdit()
        self.input_nom_client.setPlaceholderText("Ex: ClientA")
        layout_nom_c.addWidget(self.input_nom_client)
        layout_form_client.addLayout(layout_nom_c)
        
        # Port du client
        layout_port_c = QHBoxLayout()
        layout_port_c.addWidget(QLabel("Port:"))
        self.input_port_client = QLineEdit()
        self.input_port_client.setPlaceholderText("Ex: 7001")
        layout_port_c.addWidget(self.input_port_client)
        layout_form_client.addLayout(layout_port_c)
        
        # Bouton lancer client
        btn_lancer_client = QPushButton("Lancer le Client")
        btn_lancer_client.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        btn_lancer_client.clicked.connect(self.lancer_client)
        layout_form_client.addWidget(btn_lancer_client)
        
        group_client.setLayout(layout_form_client)
        layout_gerer.addWidget(group_client)
        
        # Section Processus lancés
        group_processus = QGroupBox("Information")
        layout_processus = QVBoxLayout()
        
        info_label = QLabel("Les routeurs et clients se lancent dans des terminaux séparés.\nConsultez les terminaux ouverts pour voir leur statut.")
        info_label.setStyleSheet("padding: 10px; background-color: #e8f5e9;")
        layout_processus.addWidget(info_label)
        
        group_processus.setLayout(layout_processus)
        layout_gerer.addWidget(group_processus)
        
        layout_gerer.addStretch()
        tab_gerer.setLayout(layout_gerer)
        tabs.addTab(tab_gerer, "Gerer")
        
        main_layout.addWidget(tabs)
        
        # Zone de statut
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        self.status_text.setPlaceholderText("Statut du serveur...")
        
        main_layout.addWidget(QLabel("Statut"))
        main_layout.addWidget(self.status_text)
        
        self.log_status("Interface Master initialisee")
    
    def get_db_connection(self):
        """Connexion à la DB"""
        try:
            conn = mariadb.connect(
                host=self.db_ip,
                user="toto",
                password="toto",
                database="table_routage"
            )
            return conn
        except mariadb.Error as e:
            self.log_status(f"Erreur DB : {e}")
            return None
    
    def lancer_routeur(self):
        """Lance un nouveau routeur"""
        nom = self.input_nom_routeur.text().strip()
        port = self.input_port_routeur.text().strip()
        
        if not nom or not port:
            QMessageBox.warning(self, "Erreur", "Remplissez tous les champs")
            return
        
        try:
            # Vérifier que le port est un nombre
            port_num = int(port)
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Le port doit etre un nombre")
            return
        
        # CORRECTION ICI : Utiliser python3 au lieu de python
        if sys.platform == "win32":
            # Windows
            commande = f'start cmd /k python routeur.py {nom} {port} {self.db_ip} {self.master_port}'
            subprocess.Popen(commande, shell=True)
        else:
            # Linux/Mac - CORRECTION : utiliser python3
            commande = f'python3 routeur.py {nom} {port} {self.db_ip} {self.master_port}'
            subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'{commande}; exec bash'])
        
        self.log_status(f"Terminal lance pour routeur {nom} sur port {port}")
        self.input_nom_routeur.clear()
        self.input_port_routeur.clear()
    
    def lancer_client(self):
        """Lance un nouveau client"""
        nom = self.input_nom_client.text().strip()
        port = self.input_port_client.text().strip()
        
        if not nom or not port:
            QMessageBox.warning(self, "Erreur", "Remplissez tous les champs")
            return
        
        try:
            # Vérifier que le port est un nombre
            port_num = int(port)
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Le port doit etre un nombre")
            return
        
        # CORRECTION ICI : Utiliser python3 au lieu de python
        if sys.platform == "win32":
            # Windows
            commande = f'start cmd /k python main.py {nom} {port} {self.db_ip} {self.master_port}'
            subprocess.Popen(commande, shell=True)
        else:
            # Linux/Mac - CORRECTION : utiliser python3
            commande = f'python3 main.py {nom} {port} {self.db_ip} {self.master_port}'
            subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'{commande}; exec bash'])
        
        self.log_status(f"Terminal lance pour client {nom} sur port {port}")
        self.input_nom_client.clear()
        self.input_port_client.clear()
    
    def refresh_data(self):
        """Rafraîchit toutes les données"""
        self.load_routeurs()
        self.load_clients()
        self.update_stats()
    
    def load_routeurs(self):
        """Charge les routeurs depuis la DB"""
        conn = self.get_db_connection()
        if not conn:
            return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT nom, adresse_ip, port, cle_publique FROM routeurs WHERE type='routeur'")
            rows = cur.fetchall()
            
            self.table_routeurs.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.table_routeurs.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table_routeurs.setItem(i, 1, QTableWidgetItem(str(row[1])))
                self.table_routeurs.setItem(i, 2, QTableWidgetItem(str(row[2])))
                cle = str(row[3])[:50] + "..." if row[3] and len(str(row[3])) > 50 else str(row[3])
                self.table_routeurs.setItem(i, 3, QTableWidgetItem(cle))
                
                btn_delete = QPushButton("Supprimer")
                btn_delete.clicked.connect(lambda checked, nom=str(row[0]): self.supprimer_routeur(nom))
                btn_delete.setStyleSheet("background-color: #dc3545; color: white;")
                self.table_routeurs.setCellWidget(i, 4, btn_delete)
            
            conn.close()
        except mariadb.Error as e:
            self.log_status(f"Erreur chargement routeurs : {e}")
    
    def load_clients(self):
        """Charge les clients depuis la DB"""
        conn = self.get_db_connection()
        if not conn:
            return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT nom, adresse_ip, port FROM clients")
            rows = cur.fetchall()
            
            self.table_clients.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.table_clients.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table_clients.setItem(i, 1, QTableWidgetItem(str(row[1])))
                self.table_clients.setItem(i, 2, QTableWidgetItem(str(row[2])))
                
                btn_delete = QPushButton("Supprimer")
                btn_delete.clicked.connect(lambda checked, nom=str(row[0]): self.supprimer_client(nom))
                btn_delete.setStyleSheet("background-color: #dc3545; color: white;")
                self.table_clients.setCellWidget(i, 3, btn_delete)
            
            conn.close()
        except mariadb.Error as e:
            self.log_status(f"Erreur chargement clients : {e}")
    
    def supprimer_routeur(self, nom):
        """Supprime un routeur"""
        reply = QMessageBox.question(
            self, 'Confirmation',
            f"Supprimer le routeur '{nom}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            conn = self.get_db_connection()
            if not conn:
                return
            
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM routeurs WHERE nom = %s", (nom,))
                conn.commit()
                conn.close()
                
                self.log_status(f"Routeur {nom} supprime")
                self.refresh_data()
            except mariadb.Error as e:
                self.log_status(f"Erreur suppression : {e}")
    
    def supprimer_client(self, nom):
        """Supprime un client"""
        reply = QMessageBox.question(
            self, 'Confirmation',
            f"Supprimer le client '{nom}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            conn = self.get_db_connection()
            if not conn:
                return
            
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM clients WHERE nom = %s", (nom,))
                conn.commit()
                conn.close()
                
                self.log_status(f"Client {nom} supprime")
                self.refresh_data()
            except mariadb.Error as e:
                self.log_status(f"Erreur suppression : {e}")
    
    def update_stats(self):
        """Met à jour les statistiques"""
        conn = self.get_db_connection()
        if not conn:
            return
        
        try:
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM routeurs WHERE type='routeur'")
            nb_routeurs = cur.fetchone()[0]
            self.label_nb_routeurs.setText(f"Routeurs: {nb_routeurs}")
            
            cur.execute("SELECT COUNT(*) FROM clients")
            nb_clients = cur.fetchone()[0]
            self.label_nb_clients.setText(f"Clients: {nb_clients}")
            
            conn.close()
        except mariadb.Error as e:
            self.log_status(f"Erreur stats : {e}")
    
    def log_status(self, message):
        """Ajoute un message au statut"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage : python interface_master.py <DB_IP> <MASTER_PORT>")
        sys.exit(1)
    
    db_ip = sys.argv[1]
    master_port = int(sys.argv[2])
    
    app = QApplication(sys.argv)
    window = InterfaceMaster(db_ip, master_port)
    window.show()
    sys.exit(app.exec())