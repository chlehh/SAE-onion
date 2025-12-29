import socket
import threading
import random
import sys
import time
from cryptographie import rsa_decrypt
from cryptographie import generer_cle_rsa

class Routeur:
    def __init__(self, nom, port, master_ip, master_port, pub_key, priv_key):
        self.nom = nom
        self.port = port
        self.master_ip = master_ip
        self.master_port = master_port
        self.pub_key = pub_key  # La clé publique sous forme de tuple (e, n)
        self.priv_key = priv_key  # La clé privée sous forme de tuple (d, n)
        
        # Initialisation du socket d'écoute
        self.server_socket = None
        self.running = True
        
        print(f"Routeur {self.nom} initialisé")
        print(f"   Port d'écoute : {self.port}")
        print(f"   Clé publique : {self.pub_key}")
        print(f"   Clé privée : {self.priv_key}")

    def enregistrer_aupres_master(self):
        """Enregistre le routeur auprès du serveur Master."""
        try:
            print(f"Connexion au Master ({self.master_ip}:{self.master_port})...")

            # Créer un socket pour se connecter au Master
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            
            # Créer le message d'enregistrement
            message = f"Routeur {self.nom} {self.port} {self.pub_key}"
            s.send(message.encode())
            
            # Réception de la réponse du Master
            reponse = s.recv(1024).decode()
            s.close()
            
            # Vérification de la réponse du Master
            if reponse.startswith("OK"):
                print(f"Routeur {self.nom} enregistré auprès du Master")
                return True
            else:
                print(f"Erreur lors de l'enregistrement : {reponse}")
                return False
        except socket.error as e:
            print(f"Erreur de connexion au Master : {e}")
            return False

    def dechiffrer_couche(self, message_chiffre):
        """Déchiffre UNE couche du message avec la clé privée du routeur."""
        try:
            print(f"Message brut reçu : {message_chiffre}")
        
            # Séparer le message en différentes parties : chaque nombre séparé par des virgules
            parties_chiffrees = message_chiffre.split(",")
        
            # Afficher les parties séparées
            print(f"Parties séparées : {parties_chiffrees}")
        
            # Déchiffrement de chaque partie (intégrer la clé privée pour déchiffrer)
            message_dechiffre = ""
            for partie in parties_chiffrees:
                try:
                    chiffre = int(partie)  # Convertir chaque partie en entier
                    # Déchiffrement avec la clé privée (d, n)
                    octet_dechiffre = pow(chiffre, self.priv_key[0], self.priv_key[1])
                    message_dechiffre += chr(octet_dechiffre)  # Convertir l'entier déchiffré en caractère et l'ajouter
                except ValueError as e:
                    print(f"Erreur de conversion de la partie chiffrée '{partie}': {e}")
                    continue

            print(f"Message déchiffré : {message_dechiffre}")
            
            # Séparer le prochain hop (Routeur1) et le message final
            if ":" in message_dechiffre:
                next_hop, message_final = message_dechiffre.split(":", 1)
                print(f"Next hop déchiffré : {next_hop}")
                print(f"Message final déchiffré : {message_final}")
                return next_hop, message_final
            else:
                print(f"Message final (sans prochain hop) : {message_dechiffre}")
                return "", message_dechiffre

        except Exception as e:
            print(f"Erreur lors du déchiffrement : {e}")
            return None, None

    def transmettre_message(self, next_hop, message):
        """Transmet le message au prochain routeur ou client."""
        try:
            infos = self.recuperer_infos_depuis_master(next_hop)
            
            if not infos:
                print(f"Impossible de trouver {next_hop}")
                return False
            
            ip, port = infos.split(":")
            port = int(port)
            
            print(f"Transmission vers {next_hop} ({ip}:{port})")
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            s.send(message.encode())
            s.close()
            
            print(f"Message transmis à {next_hop}")
            return True
        except socket.error as e:
            print(f"Erreur lors de la transmission à {next_hop} : {e}")
            return False
    
    def recuperer_infos_depuis_master(self, nom_entite):
        """Récupère les informations d'un routeur ou client depuis le Master."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            s.send(f"GET_INFO:{nom_entite}".encode())
            reponse = s.recv(8192).decode()
            s.close()
            
            if reponse.startswith("ERROR"):
                return None
            
            return reponse.split(":")
        except Exception as e:
            print(f"Erreur lors de la récupération des infos : {e}")
            return None
    
    def traiter_message(self, message_recu, addr):
        """Traite un message reçu."""
        print(f"\nMessage reçu de {addr}")
        
        next_hop, reste = self.dechiffrer_couche(message_recu)
        
        if next_hop is None:
            print("Impossible de déchiffrer le message")
            return
        
        print(f"Next hop déchiffré : {next_hop}")
        self.transmettre_message(next_hop, reste)
    
    def ecouter(self):
        """Écoute les messages entrants."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("0.0.0.0", self.port))
        self.server_socket.listen(5)
        
        print(f"Routeur {self.nom} en écoute sur 0.0.0.0:{self.port}")
        
        while self.running:
            conn, addr = self.server_socket.accept()
            message = conn.recv(8192).decode()
            conn.close()
            
            if message:
                self.traiter_message(message, addr)
    
    def demarrer(self):
        """Démarre le routeur."""
        print("\n" + "="*60)
        print(f"DÉMARRAGE DU ROUTEUR {self.nom}")
        print("="*60)
        
        if not self.enregistrer_aupres_master():
            print("Impossible de s'enregistrer auprès du Master")
            sys.exit(1)
        
        time.sleep(1)
        
        try:
            self.ecouter()
        except KeyboardInterrupt:
            print(f"\nArrêt du routeur {self.nom}...")
            self.running = False
    
    def arreter(self):
        """Arrête le routeur.""" 
        self.running = False
        if self.server_socket:
            self.server_socket.close()

def main():
    if len(sys.argv) != 5:
        print("Usage incorrect!")
        print("Usage : python routeur.py <NOM> <PORT> <MASTER_IP> <MASTER_PORT>")
        sys.exit(1)
    
    nom = sys.argv[1]
    port = int(sys.argv[2])
    master_ip = sys.argv[3]
    master_port = int(sys.argv[4])
    
    # Générer les clés publiques et privées pour le chiffrement RSA
    pub_key, priv_key = generer_cle_rsa()
    
    # Initialiser le routeur avec les clés
    routeur = Routeur(nom, port, master_ip, master_port, pub_key, priv_key)
    
    # Démarrer le serveur du routeur
    if routeur.demarrer():
        print(f"{nom} enregistré auprès du Master")
        print(f"{nom} en écoute sur {master_ip}:{master_port}")
        routeur.attendre_connexions()
    else:
        print(f"Erreur lors de l'enregistrement du {nom} auprès du Master")

if __name__ == "__main__":
    main()
