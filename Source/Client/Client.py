import socket
import threading
import random
from PyQt6.QtCore import QObject, pyqtSignal
from cryptographie import rsa_encrypt, rsa_decrypt

class ClientSignals(QObject):
    """Signaux pour communication entre threads"""
    message_recu = pyqtSignal(str)
    status_change = pyqtSignal(str)

class Client:
    def __init__(self, nom, port, master_ip, master_port, pub_key, priv_key):
        self.nom = nom
        self.port = port
        self.master_ip = master_ip
        self.master_port = master_port
        self.pub_key = pub_key  # La clé publique sous forme de tuple (e, n)
        self.priv_key = priv_key  # La clé privée sous forme de tuple (d, n)
        
        self.routeurs_disponibles = {}
        self.clients_disponibles = {}
        
        self.server_socket = None
        self.running = True
        
        # Signaux
        self.signals = ClientSignals()
        
        print(f"Client {self.nom} initialisé")
        print(f"   Port d'écoute : {self.port}")
    
    def enregistrer_aupres_master(self):
        """S'enregistre auprès du serveur Master."""
        try:
            print(f"\nConnexion au Master ({self.master_ip}:{self.master_port})...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            
            # Format: "Client <nom> <port>"
            message = f"Client {self.nom} {self.port}"
            s.send(message.encode())
            
            # Attendre la réponse
            reponse = s.recv(1024).decode()
            s.close()
            
            if reponse.startswith("OK"):
                print(f"Client {self.nom} enregistré auprès du Master")
                self.signals.status_change.emit(f"Enregistré auprès du Master")
                return True
            else:
                print(f"Erreur lors de l'enregistrement : {reponse}")
                self.signals.status_change.emit(f"Erreur: {reponse}")
                return False
                
        except socket.error as e:
            print(f"Erreur de connexion au Master : {e}")
            self.signals.status_change.emit(f"Erreur de connexion")
            return False
    def demarrer(self):
        """Démarre le client."""
        print(f"Début du démarrage du client {self.nom}...")
        
        # Enregistrement auprès du Master
        if not self.enregistrer_aupres_master():
            print("Impossible de s'enregistrer auprès du Master")
            return False
        
        # Si l'enregistrement a réussi, nous pouvons démarrer le client
        self.signals.status_change.emit(f"Client {self.nom} démarré avec succès.")
        print(f"Client {self.nom} démarré.")
        
        # Vous pouvez ajouter d'autres fonctionnalités ou tâches ici si nécessaire.
        
        return True    
    def recuperer_routeurs(self):
        """Récupère la liste des routeurs depuis le Master."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            
            s.send("GET_ALL".encode())
            reponse = s.recv(8192).decode()
            s.close()
            
            if "ROUTEURS:" in reponse and "CLIENTS:" in reponse:
                parts = reponse.split("|")
                
                # Parser routeurs
                routeurs_str = parts[0].replace("ROUTEURS:", "")
                self.routeurs_disponibles = {}
                if routeurs_str:
                    for routeur in routeurs_str.split(","):
                        if routeur.strip():
                            elements = routeur.split(":")
                            if len(elements) >= 4:
                                nom = elements[0]
                                self.routeurs_disponibles[nom] = {
                                    "ip": elements[1],
                                    "port": int(elements[2]),
                                    "cle_publique": int(elements[3])
                                }
                
                # Parser clients
                clients_str = parts[1].replace("CLIENTS:", "")
                self.clients_disponibles = {}
                if clients_str:
                    for client in clients_str.split(","):
                        if client.strip():
                            elements = client.split(":")
                            if len(elements) >= 3:
                                nom = elements[0]
                                self.clients_disponibles[nom] = {
                                    "ip": elements[1],
                                    "port": int(elements[2])
                                }
                
                print(f"Récupéré {len(self.routeurs_disponibles)} routeurs et {len(self.clients_disponibles)} clients")
                return True
            
            return False
            
        except Exception as e:
            print(f"Erreur lors de la récupération des routeurs : {e}")
            return False
    
    def choisir_chemin(self, nb_sauts):
        """Choisit un chemin aléatoire de routeurs."""
        if len(self.routeurs_disponibles) < nb_sauts:
            print(f"Pas assez de routeurs disponibles ({len(self.routeurs_disponibles)} < {nb_sauts})")
            return None
        
        routeurs_noms = list(self.routeurs_disponibles.keys())
        chemin = random.sample(routeurs_noms, nb_sauts)
        
        print(f"Chemin choisi : {' -> '.join(chemin)}")
        return chemin
    
    def chiffrer_message(self, message, destinataire, chemin):
        """
        Chiffre un message en plusieurs couches (oignon) - VERSION SIMPLIFIEE.
        Format: "Routeur1:Routeur2:ClientB:message"
        """
        try:
            print(f"\n[CHIFFREMENT] Début du chiffrement SIMPLIFIÉ")
            print(f"[CHIFFREMENT] Message: {message}")
            print(f"[CHIFFREMENT] Destinataire: {destinataire}")
            print(f"[CHIFFREMENT] Chemin: {chemin}")
        
            # Construction simple : chemin complet séparé par ":"
            chemin_complet = ":".join(chemin) + ":" + destinataire + ":" + message
            print(f"[CHIFFREMENT] Message complet : {chemin_complet}")
        
            # Chiffrement avec la clé publique
            message_chiffre = rsa_encrypt(chemin_complet, self.pub_key)
            print(f"[CHIFFREMENT] Message chiffré : {message_chiffre}")
        
            return message_chiffre
            
        except Exception as e:
            print(f"Erreur lors du chiffrement : {e}")
            return None

    def envoyer_message(self, destinataire, message, nb_sauts):
        """Envoie un message chiffré au destinataire via les routeurs."""
        try:
            print(f"\n[ENVOI] Début du chiffrement du message")

            # Construction du message complet avec le chemin
            message_complet = ":".join(chemin) + ":" + destinataire + ":" + message
            print(f"[ENVOI] Message complet à chiffrer : {message_complet}")
        
            # Chiffrement du message avec la clé publique
            message_chiffre = rsa_encrypt(message_complet, self.pub_key)
            print(f"[ENVOI] Message chiffré : {message_chiffre[:100]}...")  # Limité à 100 caractères pour la lisibilité
        
            # Envoi du message chiffré
            self.transmettre_message(chemin[0], message_chiffre)
        
        except Exception as e:
            print(f"Erreur lors de l'envoi du message : {e}")
            return False

    
    def envoyer_message_avec_routeurs(self, destinataire, message, routeurs_liste):
        """Envoie un message en utilisant une liste spécifique de routeurs."""
        try:
            if not routeurs_liste:
                self.signals.message_recu.emit("ERREUR: Aucun routeur spécifié")
                return False
            
            return self._envoyer_avec_chemin(destinataire, message, routeurs_liste)
            
        except Exception as e:
            print(f"Erreur lors de l'envoi : {e}")
            self.signals.message_recu.emit(f"ERREUR: {e}")
            return False
    
    def _envoyer_avec_chemin(self, destinataire, message, chemin):
        """Méthode interne pour envoyer un message avec un chemin donné."""
        try:
            print(f"\n[ENVOI] Préparation du message")
            print(f"[ENVOI] Destinataire: {destinataire}")
            print(f"[ENVOI] Message: {message}")
            print(f"[ENVOI] Chemin: {' -> '.join(chemin)}")
            
            # 1. Chiffrer le message
            message_chiffre = self.chiffrer_message(message, destinataire, chemin)
            if not message_chiffre:
                self.signals.message_recu.emit("ERREUR: Erreur de chiffrement")
                return False
            
            print(f"[ENVOI] Message chiffré: {message_chiffre[:100]}...")
            
            # 2. Envoyer au premier routeur
            premier_routeur = chemin[0]
            info_routeur = self.routeurs_disponibles[premier_routeur]
            
            print(f"[ENVOI] Envoi au premier routeur {premier_routeur}")
            print(f"[ENVOI] Destination : {info_routeur['ip']}:{info_routeur['port']}")
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((info_routeur['ip'], info_routeur['port']))
            s.send(message_chiffre.encode())
            s.close()
            
            print(f"[ENVOI] Message envoyé avec succès!")
            
            chemin_str = " -> ".join(chemin)
            self.signals.message_recu.emit(f"Message envoyé à {destinataire} via {chemin_str}")
            
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi : {e}")
            import traceback
            traceback.print_exc()
            self.signals.message_recu.emit(f"ERREUR: {e}")
            return False
