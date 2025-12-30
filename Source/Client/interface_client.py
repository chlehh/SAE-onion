#!/usr/bin/env python3
"""
interface_client.py
Interface graphique PyQt6 pour le client
"""

import threading
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, 
                             QComboBox, QSpinBox, QGroupBox, QMessageBox,
                             QCheckBox, QRadioButton, QButtonGroup, QScrollArea)
from PyQt6.QtCore import QTimer
from client import Client

class InterfaceClient(QMainWindow):
    def __init__(self, nom, port, master_ip, master_port):
        super().__init__()
        
        self.client = Client(nom, port, master_ip, master_port)
        self.routeur_checkboxes = {}  # Dictionnaire pour stocker les checkboxes des routeurs
        
        self.setWindowTitle(f"Client {nom}")
        self.setGeometry(100, 100, 900, 700)
        
        self.init_ui()
        
        # Connecter les signaux
        self.client.signals.message_recu.connect(self.afficher_message)
        self.client.signals.status_change.connect(self.changer_statut)
        
        # Timer pour rafraîchir la liste des routeurs
        self.timer = QTimer()
        self.timer.timeout.connect(self.rafraichir_routeurs)
        self.timer.start(10000)  # Toutes les 10 secondes
        
        # Demarrer le client
        if self.client.demarrer():
            self.changer_statut("Enregistre aupres du Master")
            # Rafraichir immediatement apres le demarrage
            self.rafraichir_routeurs()
        else:
            self.changer_statut("Erreur de demarrage")
    
    def init_ui(self):
        """Initialise l'interface utilisateur."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # En-tete
        header = QLabel(f"Client {self.client.nom}")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(header)
        
        # Informations du client
        info_layout = QHBoxLayout()
        self.label_info = QLabel(f"Port: {self.client.port} | Master: {self.client.master_ip}:{self.client.master_port}")
        self.label_info.setStyleSheet("color: #666; padding: 5px;")
        info_layout.addWidget(self.label_info)
        info_layout.addStretch()
        main_layout.addLayout(info_layout)
        
        # Statut
        self.label_statut = QLabel("Connexion en cours...")
        self.label_statut.setStyleSheet("padding: 5px; background-color: #fff3cd; border-radius: 3px;")
        main_layout.addWidget(self.label_statut)
        
        # Layout horizontal pour diviser en deux colonnes
        content_layout = QHBoxLayout()
        
        # Colonne gauche: Envoi de message
        left_layout = QVBoxLayout()
        
        # Groupe: Envoi de message
        group_envoi = QGroupBox("Envoyer un message")
        layout_envoi = QVBoxLayout()
        
        # Mode de selection du destinataire
        self.radio_client = QRadioButton("Selectionner un client")
        self.radio_ip = QRadioButton("Saisir IP et Port")
        self.radio_client.setChecked(True)
        self.radio_client.toggled.connect(self.toggle_mode_destinataire)
        
        layout_envoi.addWidget(self.radio_client)
        layout_envoi.addWidget(self.radio_ip)
        
        # Selection client
        self.widget_client = QWidget()
        layout_client = QHBoxLayout()
        layout_client.setContentsMargins(0, 0, 0, 0)
        layout_client.addWidget(QLabel("Client:"))
        self.combo_destinataire = QComboBox()
        self.combo_destinataire.setMinimumWidth(200)
        layout_client.addWidget(self.combo_destinataire)
        self.widget_client.setLayout(layout_client)
        layout_envoi.addWidget(self.widget_client)
        
        # Saisie IP et Port
        self.widget_ip = QWidget()
        layout_ip = QVBoxLayout()
        layout_ip.setContentsMargins(0, 0, 0, 0)
        
        layout_ip_field = QHBoxLayout()
        layout_ip_field.addWidget(QLabel("IP:"))
        self.input_ip = QLineEdit()
        self.input_ip.setPlaceholderText("192.168.1.100")
        layout_ip_field.addWidget(self.input_ip)
        layout_ip.addLayout(layout_ip_field)
        
        layout_port_field = QHBoxLayout()
        layout_port_field.addWidget(QLabel("Port:"))
        self.input_port = QLineEdit()
        self.input_port.setPlaceholderText("7002")
        layout_port_field.addWidget(self.input_port)
        layout_ip.addLayout(layout_port_field)
        
        self.widget_ip.setLayout(layout_ip)
        self.widget_ip.setVisible(False)
        layout_envoi.addWidget(self.widget_ip)
        
        # Nombre de sauts
        layout_sauts = QHBoxLayout()
        layout_sauts.addWidget(QLabel("Nombre de sauts:"))
        self.spin_sauts = QSpinBox()
        self.spin_sauts.setMinimum(1)
        self.spin_sauts.setMaximum(10)
        self.spin_sauts.setValue(3)
        self.spin_sauts.setMaximumWidth(100)
        layout_sauts.addWidget(self.spin_sauts)
        layout_sauts.addStretch()
        layout_envoi.addLayout(layout_sauts)
        
        # Message
        layout_envoi.addWidget(QLabel("Message:"))
        self.text_message = QLineEdit()
        self.text_message.setPlaceholderText("Entrez votre message ici...")
        self.text_message.returnPressed.connect(self.envoyer_message)
        layout_envoi.addWidget(self.text_message)
        
        # Boutons
        layout_boutons = QHBoxLayout()
        self.btn_envoyer = QPushButton("Envoyer")
        self.btn_envoyer.clicked.connect(self.envoyer_message)
        self.btn_envoyer.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        layout_boutons.addWidget(self.btn_envoyer)
        
        self.btn_rafraichir = QPushButton("Rafraichir")
        self.btn_rafraichir.clicked.connect(self.rafraichir_routeurs)
        layout_boutons.addWidget(self.btn_rafraichir)
        layout_envoi.addLayout(layout_boutons)
        
        group_envoi.setLayout(layout_envoi)
        left_layout.addWidget(group_envoi)
        
        # Groupe: Messages recus
        group_messages = QGroupBox("Messages recus")
        layout_messages = QVBoxLayout()
        
        self.text_messages = QTextEdit()
        self.text_messages.setReadOnly(True)
        self.text_messages.setStyleSheet("background-color: #f5f5f5; font-family: monospace;")
        layout_messages.addWidget(self.text_messages)
        
        # Bouton effacer
        btn_clear = QPushButton("Effacer")
        btn_clear.clicked.connect(self.text_messages.clear)
        layout_messages.addWidget(btn_clear)
        
        group_messages.setLayout(layout_messages)
        left_layout.addWidget(group_messages)
        
        content_layout.addLayout(left_layout, 60)  # 60% de la largeur
        
        # Colonne droite: Routeurs disponibles
        right_layout = QVBoxLayout()
        
        group_routeurs = QGroupBox("Routeurs disponibles")
        layout_routeurs = QVBoxLayout()
        
        # Label info
        info_routeurs = QLabel("Selectionner les routeurs a utiliser:")
        info_routeurs.setStyleSheet("font-style: italic; color: #666;")
        layout_routeurs.addWidget(info_routeurs)
        
        # Scroll area pour les checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.routeurs_layout = QVBoxLayout()
        self.routeurs_layout.setSpacing(5)
        scroll_content.setLayout(self.routeurs_layout)
        scroll.setWidget(scroll_content)
        layout_routeurs.addWidget(scroll)
        
        # Boutons pour tout selectionner/deselectionner
        layout_select_buttons = QHBoxLayout()
        btn_select_all = QPushButton("Tout selectionner")
        btn_select_all.clicked.connect(self.selectionner_tous_routeurs)
        layout_select_buttons.addWidget(btn_select_all)
        
        btn_deselect_all = QPushButton("Tout deselectionner")
        btn_deselect_all.clicked.connect(self.deselectionner_tous_routeurs)
        layout_select_buttons.addWidget(btn_deselect_all)
        layout_routeurs.addLayout(layout_select_buttons)
        
        group_routeurs.setLayout(layout_routeurs)
        right_layout.addWidget(group_routeurs)
        
        content_layout.addLayout(right_layout, 40)  # 40% de la largeur
        
        main_layout.addLayout(content_layout)
        
        # Charger les destinataires et routeurs
        self.rafraichir_routeurs()
    
    def toggle_mode_destinataire(self):
        """Bascule entre le mode selection client et saisie IP."""
        if self.radio_client.isChecked():
            self.widget_client.setVisible(True)
            self.widget_ip.setVisible(False)
        else:
            self.widget_client.setVisible(False)
            self.widget_ip.setVisible(True)
    
    def rafraichir_routeurs(self):
        """Rafraichit la liste des routeurs et clients."""
        self.client.recuperer_routeurs()
        
        # Mettre a jour le combo box des clients
        self.combo_destinataire.clear()
        for nom in self.client.clients_disponibles.keys():
            if nom != self.client.nom:
                self.combo_destinataire.addItem(nom)
        
        # Mettre a jour la liste des routeurs avec checkboxes
        # Sauvegarder l'etat actuel des selections
        selections_actuelles = {}
        for nom, checkbox in self.routeur_checkboxes.items():
            selections_actuelles[nom] = checkbox.isChecked()
        
        # Vider le layout
        while self.routeurs_layout.count():
            item = self.routeurs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.routeur_checkboxes.clear()
        
        # Ajouter les nouveaux routeurs
        if not self.client.routeurs_disponibles:
            label = QLabel("Aucun routeur disponible")
            label.setStyleSheet("color: #999; font-style: italic;")
            self.routeurs_layout.addWidget(label)
        else:
            for nom, info in self.client.routeurs_disponibles.items():
                checkbox = QCheckBox(f"{nom} ({info['ip']}:{info['port']})")
                # Restaurer la selection precedente si elle existait
                if nom in selections_actuelles:
                    checkbox.setChecked(selections_actuelles[nom])
                self.routeur_checkboxes[nom] = checkbox
                self.routeurs_layout.addWidget(checkbox)
        
        self.routeurs_layout.addStretch()
    
    def selectionner_tous_routeurs(self):
        """Selectionne tous les routeurs."""
        for checkbox in self.routeur_checkboxes.values():
            checkbox.setChecked(True)
    
    def deselectionner_tous_routeurs(self):
        """Deselectionne tous les routeurs."""
        for checkbox in self.routeur_checkboxes.values():
            checkbox.setChecked(False)
    
    def get_routeurs_selectionnes(self):
        """Retourne la liste des noms des routeurs selectionnes."""
        return [nom for nom, checkbox in self.routeur_checkboxes.items() if checkbox.isChecked()]
    
    def envoyer_message(self):
        """Envoie un message."""
        message = self.text_message.text()
        nb_sauts = self.spin_sauts.value()
        
        # Determiner le destinataire
        if self.radio_client.isChecked():
            destinataire = self.combo_destinataire.currentText()
            if not destinataire:
                QMessageBox.warning(self, "Erreur", "Veuillez selectionner un destinataire")
                return
        else:
            ip = self.input_ip.text().strip()
            port = self.input_port.text().strip()
            if not ip or not port:
                QMessageBox.warning(self, "Erreur", "Veuillez saisir l'IP et le port du destinataire")
                return
            try:
                port_int = int(port)
                destinataire = f"{ip}:{port_int}"
            except ValueError:
                QMessageBox.warning(self, "Erreur", "Le port doit etre un nombre")
                return
        
        if not message:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un message")
            return
        
        # Verifier les routeurs selectionnes
        routeurs_selectionnes = self.get_routeurs_selectionnes()
        
        if routeurs_selectionnes:
            # Utiliser les routeurs selectionnes
            if len(routeurs_selectionnes) < nb_sauts:
                QMessageBox.warning(self, "Erreur", 
                                  f"Pas assez de routeurs selectionnes\n({len(routeurs_selectionnes)} selectionnes < {nb_sauts} sauts)")
                return
            # Envoyer avec les routeurs selectionnes
            thread = threading.Thread(
                target=self.client.envoyer_message_avec_routeurs,
                args=(destinataire, message, routeurs_selectionnes[:nb_sauts]),
                daemon=True
            )
        else:
            # Choisir automatiquement
            if nb_sauts > len(self.client.routeurs_disponibles):
                QMessageBox.warning(self, "Erreur", 
                                  f"Pas assez de routeurs disponibles\n({len(self.client.routeurs_disponibles)} routeurs < {nb_sauts} sauts)")
                return
            thread = threading.Thread(
                target=self.client.envoyer_message,
                args=(destinataire, message, nb_sauts),
                daemon=True
            )
        
        thread.start()
        
        # Vider le champ de message
        self.text_message.clear()
    
    def afficher_message(self, message):
        """Affiche un message dans la zone de texte."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_messages.append(f"[{timestamp}] {message}")
    
    def changer_statut(self, statut):
        """Change le statut affiche."""
        self.label_statut.setText(statut)
        if "Enregistre" in statut or "connecte" in statut:
            self.label_statut.setStyleSheet("padding: 5px; background-color: #d4edda; border-radius: 3px;")
        elif "Erreur" in statut:
            self.label_statut.setStyleSheet("padding: 5px; background-color: #f8d7da; border-radius: 3px;")
        else:
            self.label_statut.setStyleSheet("padding: 5px; background-color: #fff3cd; border-radius: 3px;")
    
    def closeEvent(self, event):
        """Fermeture de la fenetre."""
        reply = QMessageBox.question(
            self,
            'Confirmation',
            'Voulez-vous vraiment quitter ?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.client.arreter()
            event.accept()
        else:
            event.ignore()