#!/usr/bin/env python3
"""
routeur.py
Routeur pour le systeme de routage en oignon
"""

import socket
import threading
import sys
import time
from cryptographie import generer_cles, dechiffrer, encoder_cle_pour_envoi

class Routeur:
    def __init__(self, nom, port, master_ip, master_port):
        self.nom = nom
        self.port = port
        self.master_ip = master_ip
        self.master_port = master_port
        
        # Generation des cles RSA
        self.cle_privee, self.cle_publique = generer_cles()
        
        self.server_socket = None
        self.running = True
        
        print(f"Routeur {self.nom} initialise")
        print(f"   Port: {self.port}")
        print(f"   Cle publique: {self.cle_publique}")
        print(f"   Cle privee: (confidentielle)")
    

    def enregistrer_aupres_master(self):
        """S'enregistre aupres du Master avec sa cle publique."""
        try:
            print(f"\nConnexion au Master ({self.master_ip}:{self.master_port})...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            
            # ✅ CORRECTION : Encoder CORRECTEMENT la clé publique
            cle_encodee = encoder_cle_pour_envoi(self.cle_publique)
            print(f"[DEBUG] Clé encodée envoyée au Master : '{cle_encodee}'")  # 🔍 LOG
            
            message = f"Routeur {self.nom} {self.port} {cle_encodee}"
            s.send(message.encode())
            
            reponse = s.recv(1024).decode()
            s.close()
            
            if reponse.startswith("OK"):
                print(f"Routeur {self.nom} enregistre")
                print(f"[DEBUG] Clé stockée : {cle_encodee}")  # 🔍 LOG
                return True
            else:
                print(f"Erreur: {reponse}")
                return False
                
        except socket.error as e:
            print(f"Erreur connexion: {e}")
            return False
    
    def dechiffrer_couche(self, message_chiffre):
        """
        Dechiffre UNE couche avec RSA.
        Format: "next_hop|message_chiffre_RSA"
        ANONYMISATION: Ne voit que le next_hop
        """
        try:
            # Separer next_hop et contenu chiffre
            if "|" not in message_chiffre:
                # Message final simple
                if ":" in message_chiffre:
                    parties = message_chiffre.split(":", 1)
                    return parties[0], parties[1] if len(parties) > 1 else ""
                return "", message_chiffre
            
            parties = message_chiffre.split("|", 1)
            next_hop = parties[0]
            contenu_chiffre = parties[1]
            
            # Dechiffrer avec RSA
            contenu_dechiffre = dechiffrer(contenu_chiffre, self.cle_privee)
            
            if contenu_dechiffre is None:
                return None, None
            
            return next_hop, contenu_dechiffre
        
        except Exception as e:
            print(f"Erreur dechiffrement: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def recuperer_infos_depuis_master(self, nom_entite):
        """
        Recupere UNIQUEMENT l'info du prochain saut.
        ANONYMISATION: Le routeur ne demande que le next_hop
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            
            s.send(f"GET_INFO:{nom_entite}".encode())
            reponse = s.recv(8192).decode()
            s.close()
            
            if reponse.startswith("ERROR"):
                return None
            
            return reponse
            
        except Exception as e:
            print(f"Erreur recuperation: {e}")
            return None
    
    def transmettre_message(self, next_hop, message):
        """Transmet au prochain saut UNIQUEMENT."""
        try:
            infos = self.recuperer_infos_depuis_master(next_hop)
            
            if not infos:
                print(f"Next hop {next_hop} introuvable")
                return False
            
            ip, port = infos.split(":")
            port = int(port)
            
            print(f"Transmission vers {next_hop} ({ip}:{port})")
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            s.send(message.encode() if isinstance(message, str) else message)
            s.close()
            
            print(f"Message transmis")
            return True
            
        except socket.error as e:
            print(f"Erreur transmission: {e}")
            return False
    
    def log_message(self, message_id):
        """Log anonyme."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((self.master_ip, self.master_port))
            
            log_msg = f"LOG {message_id} {self.nom}"
            s.send(log_msg.encode())
            s.recv(1024)
            s.close()
        except:
            pass
    
    def traiter_message(self, message_recu, addr):
        """
        Traite un message avec RSA.
        ANONYMISATION: Ne connait que le next_hop
        """
        print(f"\n{'='*60}")
        print(f"[{self.nom}] Message recu")
        print(f"{'='*60}")
        
        try:
            # Dechiffrer UNE couche RSA
            next_hop, reste = self.dechiffrer_couche(message_recu)
            
            if next_hop is None:
                print(f"[{self.nom}] Echec dechiffrement RSA")
                return
            
            print(f"[{self.nom}] Couche RSA dechiffree")
            print(f"[{self.nom}] Prochain saut: {next_hop}")
            print(f"[{self.nom}] Anonymisation: Je ne vois QUE le next_hop")
            
            # Log anonyme
            self.log_message(f"msg_{hash(message_recu) % 10000}")
            
            # Transmettre
            if next_hop and next_hop.strip():
                self.transmettre_message(next_hop, reste)
            else:
                print(f"[{self.nom}] Message final atteint")
        
        except Exception as e:
            print(f"[{self.nom}] Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    def ecouter(self):
        """Ecoute les messages."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", self.port))
            self.server_socket.listen(5)
            
            print(f"\n{self.nom} en ecoute sur 0.0.0.0:{self.port}")
            print("En attente...\n")
            
            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                    message = conn.recv(8192).decode()
                    conn.close()
                    
                    if message:
                        thread = threading.Thread(
                            target=self.traiter_message,
                            args=(message, addr),
                            daemon=True
                        )
                        thread.start()
                
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Erreur: {e}")
                    
        except Exception as e:
            print(f"Erreur demarrage: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def demarrer(self):
        """Demarre le routeur."""
        print("\n" + "="*60)
        print(f"DEMARRAGE ROUTEUR {self.nom}")
        print("="*60)
        
        if not self.enregistrer_aupres_master():
            sys.exit(1)
        
        time.sleep(1)
        
        try:
            self.ecouter()
        except KeyboardInterrupt:
            print(f"\nArret {self.nom}...")
            self.running = False


def main():
    if len(sys.argv) != 5:
        print("Usage: python routeur.py <NOM> <PORT> <MASTER_IP> <MASTER_PORT>")
        sys.exit(1)
    
    nom = sys.argv[1]
    port = int(sys.argv[2])
    master_ip = sys.argv[3]
    master_port = int(sys.argv[4])
    
    routeur = Routeur(nom, port, master_ip, master_port)
    routeur.demarrer()


if __name__ == "__main__":
    main()