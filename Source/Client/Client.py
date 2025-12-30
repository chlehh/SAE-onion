#!/usr/bin/env python3
"""
client.py
Logique metier du client pour le systeme de routage en oignon
"""

import socket
import threading
import random
from PyQt6.QtCore import QObject, pyqtSignal

class ClientSignals(QObject):
    """Signaux pour communication entre threads"""
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
        
        self.server_socket = None
        self.running = True
        
        # Signaux
        self.signals = ClientSignals()
        
        print(f"Client {self.nom} initialise")
        print(f"   Port d'ecoute : {self.port}")
    
    def enregistrer_aupres_master(self):
        """S'enregistre aupres du serveur Master."""
        try:
            print(f"\nConnexion au Master ({self.master_ip}:{self.master_port})...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            
            message = f"Client {self.nom} {self.port}"
            s.send(message.encode())
            
            reponse = s.recv(1024).decode()
            s.close()
            
            if reponse.startswith("OK"):
                print(f"Client {self.nom} enregistre aupres du Master")
                self.signals.status_change.emit(f"Enregistre aupres du Master")
                return True
            else:
                print(f"Erreur lors de l'enregistrement : {reponse}")
                self.signals.status_change.emit(f"Erreur: {reponse}")
                return False
                
        except socket.error as e:
            print(f"Erreur de connexion au Master : {e}")
            self.signals.status_change.emit(f"Erreur de connexion")
            return False
    
    def recuperer_routeurs(self):
        """Recupere routeurs et clients avec cles RSA."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            
            s.send("GET_ALL".encode())
            reponse = s.recv(8192).decode()
            s.close()
            
            print(f"[DEBUG] Reponse brute du Master: '{reponse}'")
            
            if "ROUTEURS:" in reponse and "CLIENTS:" in reponse:
                parts = reponse.split("|")
                
                # Parser routeurs
                routeurs_str = parts[0].replace("ROUTEURS:", "")
                self.routeurs_disponibles = {}
                
                print(f"[DEBUG] Chaine routeurs: '{routeurs_str}'")
                
                if routeurs_str:
                    for routeur in routeurs_str.split(";"):
                        if routeur.strip():
                            # Format attendu: nom:ip:port:cle_publique
                            #  la cle_publique contient aussi une virgule (e,n)
                           
                            
                            print(f"[DEBUG] Parsing routeur: '{routeur}'")
                            
                            # Trouver les 3 premiers ":"
                            first_colon = routeur.find(":")
                            if first_colon == -1:
                                continue
                            
                            second_colon = routeur.find(":", first_colon + 1)
                            if second_colon == -1:
                                continue
                            
                            third_colon = routeur.find(":", second_colon + 1)
                            if third_colon == -1:
                                continue
                            
                            # Extraire les parties
                            nom = routeur[:first_colon]
                            ip = routeur[first_colon + 1:second_colon]
                            port_str = routeur[second_colon + 1:third_colon]
                            cle_publique = routeur[third_colon + 1:]
                            
                            print(f"[DEBUG]   Nom: {nom}")
                            print(f"[DEBUG]   IP: {ip}")
                            print(f"[DEBUG]   Port: {port_str}")
                            print(f"[DEBUG]   Cle: '{cle_publique}'")
                            
                            try:
                                port_int = int(port_str)
                                self.routeurs_disponibles[nom] = {
                                    "ip": ip,
                                    "port": port_int,
                                    "cle_publique": cle_publique
                                }
                                print(f"[DEBUG]   -> Routeur {nom} ajoute avec succes")
                            except ValueError:
                                print(f"[ERREUR] Port invalide pour {nom}: '{port_str}'")
                                continue
                
                # Parser clients
                clients_str = parts[1].replace("CLIENTS:", "")
                self.clients_disponibles = {}
                
                print(f"[DEBUG] Chaine clients: '{clients_str}'")
                
                if clients_str:
                    for client in clients_str.split(";"):
                        if client.strip():
                            elements = client.split(":")
                            if len(elements) >= 3:
                                nom = elements[0]
                                self.clients_disponibles[nom] = {
                                    "ip": elements[1],
                                    "port": int(elements[2])
                                }
                                print(f"[DEBUG]   -> Client {nom} ajoute")
                
                print(f"Recupere: {len(self.routeurs_disponibles)} routeurs, {len(self.clients_disponibles)} clients")
                return True
            
            return False
            
        except Exception as e:
            print(f"Erreur recuperation: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def choisir_chemin(self, nb_sauts):
        """Choisit un chemin aleatoire de routeurs."""
        if len(self.routeurs_disponibles) < nb_sauts:
            print(f"Pas assez de routeurs ({len(self.routeurs_disponibles)} < {nb_sauts})")
            return None
        
        routeurs_noms = list(self.routeurs_disponibles.keys())
        chemin = random.sample(routeurs_noms, nb_sauts)
        
        print(f"Chemin choisi : {' -> '.join(chemin)}")
        return chemin
    
    def chiffrer_message(self, message, destinataire, chemin):
        """
        Chiffre avec RSA en couches (oignon).
        ANONYMISATION COMPLETE avec cryptage RSA median.
        """
        try:
            from cryptographie import chiffrer, decoder_cle_recue
            
            print(f"\n[CLIENT] Creation oignon RSA - ANONYMISATION COMPLETE")
            print(f"[CLIENT] Message: {message}")
            print(f"[CLIENT] Destinataire: {destinataire}")
            print(f"[CLIENT] Chemin: {' -> '.join(chemin)}")
            
            # Contenu initial
            contenu = f"{destinataire}:{self.nom}:{message}"
            
            # Chiffrer couche par couche avec RSA
            for i in range(len(chemin) - 1, -1, -1):
                routeur_nom = chemin[i]
                
                # Recuperer et decoder la cle publique du routeur
                cle_publique_str = self.routeurs_disponibles[routeur_nom]['cle_publique']
                
                print(f"\n[CLIENT] Traitement routeur: {routeur_nom}")
                print(f"[CLIENT] Cle brute recue: '{cle_publique_str}'")
                print(f"[CLIENT] Longueur: {len(cle_publique_str)} caracteres")
                
                # Verifier le format AVANT de decoder
                if ',' not in cle_publique_str:
                    print(f"[CLIENT] ERREUR : La cle ne contient pas de virgule !")
                    print(f"[CLIENT] Format recu : '{cle_publique_str}'")
                    print(f"[CLIENT] Format attendu : 'e,n' (ex: '65537,123456')")
                    return None
                
                cle_publique = decoder_cle_recue(cle_publique_str)
                
                if cle_publique is None:
                    print(f"[CLIENT] Erreur decodage cle {routeur_nom}")
                    print(f"[CLIENT] Cle problematique: '{cle_publique_str}'")
                    return None
                
                print(f"[CLIENT] Cle decodee : e={cle_publique[0]}, n={cle_publique[1]}")
                
                # Determiner next_hop
                if i == len(chemin) - 1:
                    next_hop = destinataire
                else:
                    next_hop = chemin[i + 1]
                
                # Chiffrer avec RSA
                contenu_chiffre = chiffrer(contenu, cle_publique)
                
                # Nouvelle couche
                contenu = f"{next_hop}|{contenu_chiffre}"
                
                print(f"[CLIENT] Couche {len(chemin) - i}: {routeur_nom}")
                print(f"[CLIENT]   -> Chiffrement RSA avec cle: {cle_publique[0]}")
                print(f"[CLIENT]   -> Voit seulement: {next_hop}")
            
            print(f"[CLIENT] Oignon RSA cree - {len(chemin)} couches")
            return contenu
        
        except Exception as e:
            print(f"[CLIENT] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def envoyer_message(self, destinataire, message, nb_sauts):
        """Envoie un message chiffre au destinataire via les routeurs."""
        try:
            # Choisir un chemin
            chemin = self.choisir_chemin(nb_sauts)
            if not chemin:
                self.signals.message_recu.emit("ERREUR: Impossible de choisir un chemin")
                return False
            
            return self._envoyer_avec_chemin(destinataire, message, chemin)
            
        except Exception as e:
            print(f"Erreur lors de l'envoi : {e}")
            self.signals.message_recu.emit(f"ERREUR: {e}")
            return False
    
    def envoyer_message_avec_routeurs(self, destinataire, message, routeurs_liste):
        """Envoie un message en utilisant une liste specifique de routeurs."""
        try:
            if not routeurs_liste:
                self.signals.message_recu.emit("ERREUR: Aucun routeur specifie")
                return False
            
            return self._envoyer_avec_chemin(destinataire, message, routeurs_liste)
            
        except Exception as e:
            print(f"Erreur lors de l'envoi : {e}")
            self.signals.message_recu.emit(f"ERREUR: {e}")
            return False
    
    def _envoyer_avec_chemin(self, destinataire, message, chemin):
        """Methode interne pour envoyer un message avec un chemin donne"""
        try:
            print(f"\n[ENVOI] Preparation du message")
            print(f"[ENVOI] Destinataire: {destinataire}")
            print(f"[ENVOI] Message: {message}")
            print(f"[ENVOI] Chemin: {' -> '.join(chemin)}")
            
            # Chiffrer le message
            message_chiffre = self.chiffrer_message(message, destinataire, chemin)
            if not message_chiffre:
                self.signals.message_recu.emit("ERREUR: Erreur de chiffrement")
                return False
            
            print(f"[ENVOI] Message chiffre: {message_chiffre[:100]}...")
            
            # Envoyer au premier routeur
            premier_routeur = chemin[0]
            info_routeur = self.routeurs_disponibles[premier_routeur]
            
            print(f"[ENVOI] Envoi au premier routeur {premier_routeur}")
            print(f"[ENVOI] Destination : {info_routeur['ip']}:{info_routeur['port']}")
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((info_routeur['ip'], info_routeur['port']))
            s.send(message_chiffre.encode())
            s.close()
            
            print(f"[ENVOI] Message envoye avec succes!")
            
            chemin_str = " -> ".join(chemin)
            self.signals.message_recu.emit(f"Message envoye a {destinataire} via {chemin_str}")
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'envoi : {e}")
            import traceback
            traceback.print_exc()
            self.signals.message_recu.emit(f"ERREUR: {e}")
            return False
    
    def ecouter(self):
        """Ecoute les messages entrants."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", self.port))
            self.server_socket.listen(5)
            
            print(f"\nClient {self.nom} en ecoute sur 0.0.0.0:{self.port}")
            
            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                    message = conn.recv(8192).decode()
                    conn.close()
                    
                    if message:
                        print(f"\nMessage recu de {addr}")
                        print(f"   Contenu : {message}")
                        
                        # Parser le message final
                    if ":" in message:
                        parts = message.split(":", 2)  # Split en 3 parties
                        if len(parts) >= 3:
                            # parts[0] = destinataire
                            # parts[1] = expéditeur 
                            # parts[2] = message
                            expediteur = parts[1]
                            contenu = parts[2]
                            self.signals.message_recu.emit(f"De {expediteur}: {contenu}")
                        elif len(parts) >= 2:
                            # Format ancien (compatibilité)
                            contenu = parts[1]
                            self.signals.message_recu.emit(f"Message recu: {contenu}")
                        else:
                            self.signals.message_recu.emit(f"Message: {message}")
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Erreur lors de la reception : {e}")
                    
        except Exception as e:
            print(f"Erreur lors du demarrage de l'ecoute : {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def demarrer(self):
        """Demarre le client."""
        if not self.enregistrer_aupres_master():
            return False
        
        import time
        time.sleep(1)
        
        self.recuperer_routeurs()
        
        thread_ecoute = threading.Thread(target=self.ecouter, daemon=True)
        thread_ecoute.start()
        
        return True
    
    def arreter(self):
        """Arrete le client."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()