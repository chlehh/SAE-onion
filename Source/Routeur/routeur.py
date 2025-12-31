#!/usr/bin/env python3
"""Routeur pour routage en oignon"""

import socket
import threading
import sys
from cryptographie import generer_cles, dechiffrer, encoder_cle_pour_envoi

class Routeur:
    def __init__(self, nom, port, master_ip, master_port):
        self.nom = nom
        self.port = port
        self.master_ip = master_ip
        self.master_port = master_port
        
        self.cle_privee, self.cle_publique = generer_cles()
        self.running = True
        
        print(f"Routeur {nom} initialise (port {port})")
    
    def enregistrer_aupres_master(self):
        """S'enregistre au Master"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            
            cle_str = encoder_cle_pour_envoi(self.cle_publique)
            message = f"Routeur {self.nom} {self.port} {cle_str}"
            s.send(message.encode('utf-8'))
            
            reponse = s.recv(1024).decode('utf-8', errors='ignore')
            s.close()
            
            if reponse.startswith("OK"):
                print(f"Enregistre aupres du Master")
                return True
            return False
        except:
            return False
    
    def dechiffrer_couche(self, message_chiffre):
        """Dechiffre une couche RSA"""
        try:
            if "|" not in message_chiffre:
                return "", message_chiffre
            
            next_hop, contenu_chiffre = message_chiffre.split("|", 1)
            contenu_dechiffre = dechiffrer(contenu_chiffre, self.cle_privee)
            
            return next_hop, contenu_dechiffre
        except:
            return None, None
    
    def get_info_next_hop(self, nom):
        """Recupere IP:PORT du prochain saut"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            s.send(f"GET_INFO:{nom}".encode('utf-8'))
            
            reponse = s.recv(8192).decode('utf-8', errors='ignore')
            s.close()
            
            return None if reponse.startswith("ERROR") else reponse
        except:
            return None
    
    def transmettre(self, next_hop, message):
        """Transmet au prochain saut"""
        try:
            infos = self.get_info_next_hop(next_hop)
            if not infos:
                return False
            
            ip, port = infos.split(":")
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, int(port)))
            s.send(message.encode('utf-8'))
            s.close()
            
            print(f"Transmis a {next_hop}")
            return True
        except:
            return False
    
    def traiter_message(self, message_recu):
        """Traite un message recu"""
        print(f"\n[{self.nom}] Message recu")
        
        next_hop, reste = self.dechiffrer_couche(message_recu)
        
        if next_hop is None:
            print("Echec dechiffrement")
            return
        
        print(f"Dechiffre -> next_hop: {next_hop}")
        
        if next_hop and next_hop.strip():
            self.transmettre(next_hop, reste)
        else:
            print("Message final")
    
    def ecouter(self):
        """Ecoute les messages entrants"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self.port))
        server.listen(5)
        
        print(f"En ecoute sur port {self.port}\n")
        
        while self.running:
            try:
                conn, addr = server.accept()
                message = conn.recv(8192).decode('utf-8', errors='ignore')
                conn.close()
                
                if message:
                    threading.Thread(
                        target=self.traiter_message,
                        args=(message,),
                        daemon=True
                    ).start()
            except:
                continue
    
    def demarrer(self):
        """Demarre le routeur"""
        if not self.enregistrer_aupres_master():
            print("Erreur enregistrement")
            return
        
        try:
            self.ecouter()
        except KeyboardInterrupt:
            print("\nArret")
            self.running = False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python routeur.py <NOM> <PORT> <MASTER_IP> <MASTER_PORT>")
        sys.exit(1)
    
    routeur = Routeur(sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]))
    routeur.demarrer()