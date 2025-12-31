#!/usr/bin/env python3
"""Client pour routage en oignon"""

import socket
import threading
import random
from PyQt6.QtCore import QObject, pyqtSignal

class ClientSignals(QObject):
    message_recu = pyqtSignal(str)
    status_change = pyqtSignal(str)

class Client:
    def __init__(self, nom, port, master_ip, master_port):
        self.nom = nom
        self.port = port
        self.master_ip = master_ip
        self.master_port = master_port
        
        self.routeurs_disponibles = {}
        self.clients_disponibles = {}
        self.running = True
        self.signals = ClientSignals()
        
        print(f"Client {nom} initialise (port {port})")
    
    def enregistrer_aupres_master(self):
        """S'enregistre au Master"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            
            message = f"Client {self.nom} {self.port}"
            s.send(message.encode('utf-8'))
            
            reponse = s.recv(1024).decode('utf-8', errors='ignore')
            s.close()
            
            if reponse.startswith("OK"):
                self.signals.status_change.emit("Enregistre")
                return True
            return False
        except:
            return False
    
    def recuperer_routeurs(self):
        """Recupere routeurs et clients"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            s.send("GET_ALL".encode('utf-8'))
            
            reponse = s.recv(8192).decode('utf-8', errors='ignore')
            s.close()
            
            if "ROUTEURS:" not in reponse or "CLIENTS:" not in reponse:
                return False
            
            parts = reponse.split("|")
            
            # Parser routeurs
            routeurs_str = parts[0].replace("ROUTEURS:", "")
            self.routeurs_disponibles = {}
            
            if routeurs_str:
                for routeur in routeurs_str.split(";"):
                    if not routeur.strip():
                        continue
                    
                    idx1 = routeur.find(":")
                    idx2 = routeur.find(":", idx1 + 1)
                    idx3 = routeur.find(":", idx2 + 1)
                    
                    if idx1 == -1 or idx2 == -1 or idx3 == -1:
                        continue
                    
                    nom = routeur[:idx1]
                    ip = routeur[idx1+1:idx2]
                    port = int(routeur[idx2+1:idx3])
                    cle = routeur[idx3+1:]
                    
                    self.routeurs_disponibles[nom] = {
                        "ip": ip,
                        "port": port,
                        "cle_publique": cle
                    }
            
            # Parser clients
            clients_str = parts[1].replace("CLIENTS:", "")
            self.clients_disponibles = {}
            
            if clients_str:
                for client in clients_str.split(";"):
                    if not client.strip():
                        continue
                    
                    elements = client.split(":")
                    if len(elements) >= 3:
                        nom = elements[0]
                        self.clients_disponibles[nom] = {
                            "ip": elements[1],
                            "port": int(elements[2])
                        }
            
            print(f"Recupere: {len(self.routeurs_disponibles)} routeurs, {len(self.clients_disponibles)} clients")
            return True
        except Exception as e:
            print(f"Erreur recuperation: {e}")
            return False
    
    def choisir_chemin(self, nb_sauts):
        """Choisit un chemin aleatoire"""
        if len(self.routeurs_disponibles) < nb_sauts:
            return None
        
        routeurs = list(self.routeurs_disponibles.keys())
        return random.sample(routeurs, nb_sauts)
    
    def chiffrer_message(self, message, destinataire, chemin):
        """Chiffre en couches (oignon)"""
        try:
            from cryptographie import chiffrer, decoder_cle_recue
            
            contenu = f"{destinataire}:{self.nom}:{message}"
            
            for i in range(len(chemin) - 1, -1, -1):
                routeur_nom = chemin[i]
                cle_str = self.routeurs_disponibles[routeur_nom]['cle_publique']
                
                if ',' not in cle_str:
                    print(f"Cle mal formatee pour {routeur_nom}")
                    return None
                
                cle_publique = decoder_cle_recue(cle_str)
                if not cle_publique:
                    return None
                
                next_hop = destinataire if i == len(chemin) - 1 else chemin[i + 1]
                
                contenu_chiffre = chiffrer(contenu, cle_publique)
                contenu = f"{next_hop}|{contenu_chiffre}"
            
            return contenu
        except Exception as e:
            print(f"Erreur chiffrement: {e}")
            return None
    
    def envoyer_message(self, destinataire, message, nb_sauts):
        """Envoie un message"""
        chemin = self.choisir_chemin(nb_sauts)
        if not chemin:
            self.signals.message_recu.emit("Pas assez de routeurs")
            return False
        
        return self._envoyer_avec_chemin(destinataire, message, chemin)
    
    def envoyer_message_avec_routeurs(self, destinataire, message, routeurs_liste):
        """Envoie avec routeurs specifiques"""
        if not routeurs_liste:
            self.signals.message_recu.emit("Aucun routeur")
            return False
        
        return self._envoyer_avec_chemin(destinataire, message, routeurs_liste)
    
    def _envoyer_avec_chemin(self, destinataire, message, chemin):
        """Envoie via un chemin donne"""
        try:
            message_chiffre = self.chiffrer_message(message, destinataire, chemin)
            if not message_chiffre:
                self.signals.message_recu.emit("Erreur chiffrement")
                return False
            
            premier = chemin[0]
            info = self.routeurs_disponibles[premier]
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((info['ip'], info['port']))
            s.send(message_chiffre.encode('utf-8'))
            s.close()
            
            chemin_str = " -> ".join(chemin)
            self.signals.message_recu.emit(f"Envoye a {destinataire} via {chemin_str}")
            return True
        except Exception as e:
            print(f"Erreur envoi: {e}")
            return False
    
    def ecouter(self):
        """Ecoute les messages entrants"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self.port))
        server.listen(5)
        
        print(f"En ecoute sur port {self.port}")
        
        while self.running:
            try:
                conn, addr = server.accept()
                message = conn.recv(8192).decode('utf-8', errors='ignore')
                conn.close()
                
                if message and ":" in message:
                    parts = message.split(":", 2)
                    if len(parts) >= 3:
                        expediteur = parts[1]
                        contenu = parts[2]
                        self.signals.message_recu.emit(f"De {expediteur}: {contenu}")
            except Exception as e:
                print(f"Erreur reception: {e}")
                continue
    
    def demarrer(self):
        """Demarre le client"""
        if not self.enregistrer_aupres_master():
            return False
        
        self.recuperer_routeurs()
        
        threading.Thread(target=self.ecouter, daemon=True).start()
        return True
    
    def arreter(self):
        """Arrete le client"""
        self.running = False