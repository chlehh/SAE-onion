#!/usr/bin/env python3
"""
interface_master.py
Interface graphique pour le serveur Master
"""

import sys
import mariadb
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QTableWidget, QTableWidgetItem, QTabWidget, 
                             QGroupBox, QMessageBox)
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QFont

class InterfaceMaster(QMainWindow):
    signal_connexion = pyqtSignal()
    
    def __init__(self, db_ip, master_port):
        super().__init__()
        self.db_ip = db_ip
        self.master_port = master_port
        
        self.setWindowTitle(f"Serveur Master - Port {master_port}")
        self.setGeometry(100, 100, 1000, 700)
        
        self.init_ui()
        
        # Timer pour rafraîchir les données toutes les 5 secondes
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(5000)
        
        # Charger les données initiales
        self.refresh_data()
    
    def init_ui(self):
        """Initialise l'interface utilisateur."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # En-tete
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Serveur Master - Routage en Oignon")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Informations de connexion
        info_label = QLabel(f"DB: {self.db_ip} | Port: {self.master_port}")
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(info_label)
        
        main_layout.addLayout(header_layout)
        
        # Statistiques rapides
        stats_group = QGroupBox("Statistiques")
        stats_layout = QHBoxLayout()
        
        self.label_nb_routeurs = QLabel("Routeurs: 0")
        self.label_nb_routeurs.setStyleSheet("font-size: 14px; padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
        stats_layout.addWidget(self.label_nb_routeurs)
        
        self.label_nb_clients = QLabel("Clients: 0")
        self.label_nb_clients.setStyleSheet("font-size: 14px; padding: 10px; background-color: #f3e5f5; border-radius: 5px;")
        stats_layout.addWidget(self.label_nb_clients)
        
        self.label_nb_logs = QLabel("Logs: 0")
        self.label_nb_logs.setStyleSheet("font-size: 14px; padding: 10px; background-color: #e8f5e9; border-radius: 5px;")
        stats_layout.addWidget(self.label_nb_logs)
        
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        # Onglets
        tabs = QTabWidget()
        
        # Onglet Routeurs
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
        
        layout_routeurs.addWidget(QLabel("Routeurs Actifs"))
        layout_routeurs.addWidget(self.table_routeurs)
        
        btn_refresh_routeurs = QPushButton("Rafraichir")
        btn_refresh_routeurs.clicked.connect(self.refresh_data)
        layout_routeurs.addWidget(btn_refresh_routeurs)
        
        tab_routeurs.setLayout(layout_routeurs)
        tabs.addTab(tab_routeurs, "Routeurs")
        
        # Onglet Clients
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
        
        # Onglet Logs
        tab_logs = QWidget()
        layout_logs = QVBoxLayout()
        
        self.table_logs = QTableWidget()
        self.table_logs.setColumnCount(4)
        self.table_logs.setHorizontalHeaderLabels(["ID", "Message ID", "Routeur", "Timestamp"])
        self.table_logs.setColumnWidth(0, 80)
        self.table_logs.setColumnWidth(1, 200)
        self.table_logs.setColumnWidth(2, 150)
        self.table_logs.setColumnWidth(3, 200)
        
        layout_logs.addWidget(QLabel("Logs des Messages"))
        layout_logs.addWidget(self.table_logs)
        
        btn_layout = QHBoxLayout()
        btn_refresh_logs = QPushButton("Rafraichir")
        btn_refresh_logs.clicked.connect(self.refresh_data)
        btn_layout.addWidget(btn_refresh_logs)
        
        btn_clear_logs = QPushButton("Effacer les logs")
        btn_clear_logs.clicked.connect(self.clear_logs)
        btn_layout.addWidget(btn_clear_logs)
        
        layout_logs.addLayout(btn_layout)
        
        tab_logs.setLayout(layout_logs)
        tabs.addTab(tab_logs, "Logs")
        
        main_layout.addWidget(tabs)
        
        # Zone de statut
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        self.status_text.setPlaceholderText("Statut du serveur...")
        
        main_layout.addWidget(QLabel("Statut"))
        main_layout.addWidget(self.status_text)
        
        self.log_status("Interface Master initialisee")
        self.log_status(f"En attente de connexions sur le port {self.master_port}")
    
    def get_db_connection(self):
        """Retourne une connexion a la base de donnees."""
        try:
            conn = mariadb.connect(
                host=self.db_ip,
                user="toto",
                password="toto",
                database="table_routage"
            )
            return conn
        except mariadb.Error as e:
            self.log_status(f"Erreur de connexion a la DB : {e}")
            return None
    
    def refresh_data(self):
        """Rafraîchit toutes les données depuis la base de données."""
        self.load_routeurs()
        self.load_clients()
        self.load_logs()
        self.update_stats()
    
    def load_routeurs(self):
        """Charge les routeurs depuis la base de donnees."""
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
                
                # Bouton supprimer
                btn_delete = QPushButton("Supprimer")
                btn_delete.clicked.connect(lambda checked, nom=str(row[0]): self.supprimer_routeur(nom))
                btn_delete.setStyleSheet("background-color: #dc3545; color: white;")
                self.table_routeurs.setCellWidget(i, 4, btn_delete)
            
            conn.close()
        except mariadb.Error as e:
            self.log_status(f"Erreur lors du chargement des routeurs : {e}")
    
    def load_clients(self):
        """Charge les clients depuis la base de donnees."""
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
                
                # Bouton supprimer
                btn_delete = QPushButton("Supprimer")
                btn_delete.clicked.connect(lambda checked, nom=str(row[0]): self.supprimer_client(nom))
                btn_delete.setStyleSheet("background-color: #dc3545; color: white;")
                self.table_clients.setCellWidget(i, 3, btn_delete)
            
            conn.close()
        except mariadb.Error as e:
            self.log_status(f"Erreur lors du chargement des clients : {e}")
    
    def load_logs(self):
        """Charge les logs depuis la base de données."""
        conn = self.get_db_connection()
        if not conn:
            return
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, message_id, routeur, timestamp FROM logs ORDER BY timestamp DESC LIMIT 100")
            rows = cur.fetchall()
            
            self.table_logs.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.table_logs.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table_logs.setItem(i, 1, QTableWidgetItem(str(row[1])))
                self.table_logs.setItem(i, 2, QTableWidgetItem(str(row[2])))
                self.table_logs.setItem(i, 3, QTableWidgetItem(str(row[3])))
            
            conn.close()
        except mariadb.Error as e:
            self.log_status(f"Erreur lors du chargement des logs : {e}")
    
    def supprimer_routeur(self, nom):
        """Supprime un routeur de la base de donnees."""
        reply = QMessageBox.question(
            self,
            'Confirmation',
            f"Voulez-vous vraiment supprimer le routeur '{nom}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
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
                self.log_status(f"Erreur lors de la suppression du routeur : {e}")
    
    def supprimer_client(self, nom):
        """Supprime un client de la base de donnees."""
        reply = QMessageBox.question(
            self,
            'Confirmation',
            f"Voulez-vous vraiment supprimer le client '{nom}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
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
                self.log_status(f"Erreur lors de la suppression du client : {e}")
    
    def update_stats(self):
        """Met à jour les statistiques."""
        conn = self.get_db_connection()
        if not conn:
            return
        
        try:
            cur = conn.cursor()
            
            # Nombre de routeurs
            cur.execute("SELECT COUNT(*) FROM routeurs WHERE type='routeur'")
            nb_routeurs = cur.fetchone()[0]
            self.label_nb_routeurs.setText(f"Routeurs: {nb_routeurs}")
            
            # Nombre de clients
            cur.execute("SELECT COUNT(*) FROM clients")
            nb_clients = cur.fetchone()[0]
            self.label_nb_clients.setText(f"Clients: {nb_clients}")
            
            # Nombre de logs
            cur.execute("SELECT COUNT(*) FROM logs")
            nb_logs = cur.fetchone()[0]
            self.label_nb_logs.setText(f"Logs: {nb_logs}")
            
            conn.close()
        except mariadb.Error as e:
            self.log_status(f"Erreur lors de la mise a jour des stats : {e}")
    
    def clear_logs(self):
        """Efface tous les logs de la base de données."""
        reply = QMessageBox.question(
            self, 
            'Confirmation', 
            "Êtes-vous sûr de vouloir effacer tous les logs ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            conn = self.get_db_connection()
            if not conn:
                return
            
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM logs")
                conn.commit()
                conn.close()
                
                self.log_status("Logs effac es avec succes")
                self.refresh_data()
            except mariadb.Error as e:
                self.log_status(f"Erreur lors de l'effacement des logs : {e}")
    
    def log_status(self, message):
        """Ajoute un message dans la zone de statut."""
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