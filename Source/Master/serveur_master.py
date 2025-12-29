#!/usr/bin/env python3
"""
serveur_master.py
Serveur Master pour le routage en oignon
"""

import socket
import mariadb
import sys
import time
import threading

def get_db_connection(db_ip):
    """Retourne une connexion à la base de données."""
    try:
        conn = mariadb.connect(
            host=db_ip,
            user="toto",
            password="toto",
            database="table_routage"
        )
        return conn
    except mariadb.Error as e:
        print(f"Erreur de connexion à la base de données : {e}")
        return None

def enregistrer_routeur(nom_routeur, ip_routeur, port_routeur, cle_publique, db_ip):
    """Enregistre un routeur dans la table 'routeurs' de la base de données."""
    try:
        conn = get_db_connection(db_ip)
        if not conn:
            return False
        
        cur = conn.cursor()
        
        # Vérifier si le routeur existe déjà
        cur.execute("SELECT id FROM routeurs WHERE nom = %s", (nom_routeur,))
        exists = cur.fetchone()
        
        if exists:
            # Mettre à jour le routeur existant
            cur.execute("""
                UPDATE routeurs 
                SET adresse_ip = %s, port = %s, cle_publique = %s, type = 'routeur'
                WHERE nom = %s
            """, (ip_routeur, port_routeur, cle_publique, nom_routeur))
            print(f"Routeur {nom_routeur} mis à jour dans la base de données")
        else:
            # Insérer un nouveau routeur
            cur.execute("""
                INSERT INTO routeurs (nom, adresse_ip, port, type, cle_publique)
                VALUES (%s, %s, %s, 'routeur', %s)
            """, (nom_routeur, ip_routeur, port_routeur, cle_publique))
            print(f"Routeur {nom_routeur} enregistré dans la base de données")
        
        conn.commit()
        conn.close()
        return True
    except mariadb.Error as e:
        print(f"Erreur lors de l'enregistrement du routeur : {e}")
        return False

def enregistrer_client(nom_client, ip_client, port_client, db_ip):
    """Enregistre un client dans la table 'clients' de la base de données."""
    try:
        conn = get_db_connection(db_ip)
        if not conn:
            return False
        
        cur = conn.cursor()
        
        # Vérifier si le client existe déjà
        cur.execute("SELECT id FROM clients WHERE nom = %s", (nom_client,))
        exists = cur.fetchone()
        
        if exists:
            # Mettre à jour le client existant
            cur.execute("""
                UPDATE clients 
                SET adresse_ip = %s, port = %s
                WHERE nom = %s
            """, (ip_client, port_client, nom_client))
            print(f"Client {nom_client} mis à jour dans la base de données")
        else:
            # Insérer un nouveau client
            cur.execute("""
                INSERT INTO clients (nom, adresse_ip, port)
                VALUES (%s, %s, %s)
            """, (nom_client, ip_client, port_client))
            print(f"Client {nom_client} enregistré dans la base de données")
        
        conn.commit()
        conn.close()
        return True
    except mariadb.Error as e:
        print(f"Erreur lors de l'enregistrement du client : {e}")
        return False

def check_routeur_status(routeur_ip, routeur_port):
    """Vérifie si un routeur est toujours en ligne en essayant de se connecter à son adresse IP et son port."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((routeur_ip, routeur_port))
        s.close()
        return True
    except (socket.error, socket.timeout):
        return False

def check_client_status(client_ip, client_port):
    """Vérifie si un client est toujours en ligne en essayant de se connecter à son adresse IP et son port."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((client_ip, client_port))
        s.close()
        return True
    except (socket.error, socket.timeout):
        return False

def remove_inactive_routeur(routeur_nom, db_ip):
    """Supprime un routeur inactif de la base de données."""
    try:
        conn = get_db_connection(db_ip)
        if not conn:
            return False
        
        cur = conn.cursor()
        cur.execute("DELETE FROM routeurs WHERE nom = %s", (routeur_nom,))
        conn.commit()
        conn.close()
        print(f"Routeur {routeur_nom} supprimé de la base de données (inactif)")
        return True
    except mariadb.Error as e:
        print(f"Erreur lors de la suppression du routeur : {e}")
        return False

def remove_inactive_client(client_nom, db_ip):
    """Supprime un client inactif de la base de données."""
    try:
        conn = get_db_connection(db_ip)
        if not conn:
            return False
        
        cur = conn.cursor()
        cur.execute("DELETE FROM clients WHERE nom = %s", (client_nom,))
        conn.commit()
        conn.close()
        print(f"Client {client_nom} supprimé de la base de données (inactif)")
        return True
    except mariadb.Error as e:
        print(f"Erreur lors de la suppression du client : {e}")
        return False

def recup_routeurs(db_ip):
    """Récupère les informations des routeurs depuis la base de données."""
    try:
        conn = get_db_connection(db_ip)
        if not conn:
            return {}
        
        cur = conn.cursor()
        cur.execute("SELECT nom, adresse_ip, port, cle_publique FROM routeurs WHERE type='routeur'")
        rows_routeurs = cur.fetchall()
        conn.close()

        routeurs = {}
        for nom, ip, port, cle_publique in rows_routeurs:
            routeurs[nom] = {
                "ip": ip, 
                "port": port, 
                "cle_publique": cle_publique if cle_publique else ""
            }

        return routeurs

    except mariadb.Error as e:
        print(f"Erreur lors de la récupération des routeurs : {e}")
        return {}

def recup_clients(db_ip):
    """Récupère les informations des clients depuis la base de données."""
    try:
        conn = get_db_connection(db_ip)
        if not conn:
            return {}
        
        cur = conn.cursor()
        cur.execute("SELECT nom, adresse_ip, port FROM clients")
        rows_clients = cur.fetchall()
        conn.close()

        clients = {}
        for nom, ip, port in rows_clients:
            clients[nom] = {"ip": ip, "port": port}

        return clients

    except mariadb.Error as e:
        print(f"Erreur lors de la récupération des clients : {e}")
        return {}

def log_message(message_id, routeur, db_ip):
    """Enregistre un message dans la table 'logs' de la base de données."""
    try:
        conn = get_db_connection(db_ip)
        if not conn:
            return False
        
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO logs (message_id, routeur)
            VALUES (%s, %s)
        """, (message_id, routeur))
        
        conn.commit()
        conn.close()
        return True
    except mariadb.Error as e:
        print(f"Erreur lors de l'enregistrement du log : {e}")
        return False

def handle_client_connection(conn, addr, db_ip):
    """Gère la connexion d'un client ou routeur et traite les demandes."""
    try:
        data = conn.recv(4096).decode()
        print(f"Reçu de {addr}: {data}")

        if data.startswith("Routeur"):
            parts = data.split(maxsplit=3)
            if len(parts) >= 4:
                nom_routeur = parts[1]
                port_routeur = int(parts[2])
                cle_publique = parts[3]
                ip_routeur = addr[0]

                success = enregistrer_routeur(nom_routeur, ip_routeur, port_routeur, cle_publique, db_ip)
                
                if success:
                    response = "OK:Routeur enregistré"
                else:
                    response = "ERROR:Échec enregistrement"
                
                conn.send(response.encode())
            else:
                conn.send("ERROR:Format invalide".encode())

        elif data.startswith("Client"):
            parts = data.split()
            if len(parts) >= 3:
                nom_client = parts[1]
                port_client = int(parts[2])
                ip_client = addr[0]

                success = enregistrer_client(nom_client, ip_client, port_client, db_ip)
                
                if success:
                    response = "OK:Client enregistré"
                else:
                    response = "ERROR:Échec enregistrement"
                
                conn.send(response.encode())
            else:
                conn.send("ERROR:Format invalide".encode())

        elif data == "GET_ROUTEURS":
            routeurs = recup_routeurs(db_ip)
            response = json.dumps(routeurs)
            conn.send(response.encode())
            print(f"Liste des routeurs envoyée à {addr}")

        elif data == "GET_CLIENTS":
            clients = recup_clients(db_ip)
            response = json.dumps(clients)
            conn.send(response.encode())
            print(f"Liste des clients envoyée à {addr}")

        elif data == "GET_ALL":
            routeurs = recup_routeurs(db_ip)
            clients = recup_clients(db_ip)
            
            routeurs_str = ",".join([
                f"{nom}:{info['ip']}:{info['port']}:{info['cle_publique']}"
                for nom, info in routeurs.items()
            ])
            
            clients_str = ",".join([
                f"{nom}:{info['ip']}:{info['port']}"
                for nom, info in clients.items()
            ])
            
            response = f"ROUTEURS:{routeurs_str}|CLIENTS:{clients_str}"
            conn.send(response.encode())
            print(f"Liste complète envoyée à {addr}")

        elif data.startswith("LOG"):
            parts = data.split()
            if len(parts) >= 3:
                message_id = parts[1]
                routeur = parts[2]
                log_message(message_id, routeur, db_ip)
                conn.send("OK:Log enregistré".encode())
            else:
                conn.send("ERROR:Format invalide".encode())

        elif data.startswith("GET_INFO"):
            parts = data.split(":", 1)
            if len(parts) >= 2:
                nom_entite = parts[1]
                
                routeurs = recup_routeurs(db_ip)
                if nom_entite in routeurs:
                    info = routeurs[nom_entite]
                    response = f"{info['ip']}:{info['port']}"
                    conn.send(response.encode())
                    print(f"Info de {nom_entite} envoyée à {addr}")
                else:
                    clients = recup_clients(db_ip)
                    if nom_entite in clients:
                        info = clients[nom_entite]
                        response = f"{info['ip']}:{info['port']}"
                        conn.send(response.encode())
                        print(f"Info de {nom_entite} envoyée à {addr}")
                    else:
                        conn.send("ERROR:Entité non trouvée".encode())
            else:
                conn.send("ERROR:Format invalide".encode())

        else:
            conn.send("ERROR:Commande inconnue".encode())

    except Exception as e:
        print(f"Erreur lors du traitement de la connexion : {e}")
    finally:
        conn.close()

def master(db_ip, master_port):
    """Serveur Master qui gère les demandes des clients et routeurs."""
    host = "0.0.0.0"
    port = master_port

    print(f"MASTER en écoute sur {host}:{port}...")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((host, port))
        server.listen(5)
        print(f"Serveur Master démarré avec succès sur {host}:{port}\n")
    except socket.error as e:
        print(f"Erreur lors de l'ouverture du port {port}: {e}")
        sys.exit(1)

    while True:
        try:
            conn, addr = server.accept()
            print(f"Nouvelle connexion de : {addr}")
            
            client_thread = threading.Thread(
                target=handle_client_connection, 
                args=(conn, addr, db_ip),
                daemon=True
            )
            client_thread.start()

        except socket.error as e:
            print(f"Erreur de connexion avec le client : {e}")
        except KeyboardInterrupt:
            print("\nArrêt du serveur Master...")
            break

    server.close()

def monitor_routeurs(db_ip, interval=60):
    """Surveille les routeurs et clients actifs et supprime ceux qui sont inactifs."""
    while True:
        try:
            print("\n=== Vérification des routeurs et clients ===")
            conn = get_db_connection(db_ip)
            if not conn:
                time.sleep(interval)
                continue
            
            cur = conn.cursor()
            
            # Vérifier les routeurs
            cur.execute("SELECT nom, adresse_ip, port FROM routeurs WHERE type = 'routeur'")
            routeurs = cur.fetchall()
            
            # Vérifier les clients
            cur.execute("SELECT nom, adresse_ip, port FROM clients")
            clients = cur.fetchall()
            
            conn.close()

            # Vérifier routeurs
            for routeur in routeurs:
                nom, ip, port = routeur
                print(f"  Vérification du routeur {nom} - {ip}:{port}")
                if not check_routeur_status(ip, port):
                    print(f"  {nom} est inactif. Suppression...")
                    remove_inactive_routeur(nom, db_ip)
                else:
                    print(f"  {nom} est actif.")
            
            # Vérifier clients
            for client in clients:
                nom, ip, port = client
                print(f"  Vérification du client {nom} - {ip}:{port}")
                if not check_client_status(ip, port):
                    print(f"  {nom} est inactif. Suppression...")
                    remove_inactive_client(nom, db_ip)
                else:
                    print(f"  {nom} est actif.")

            print(f"\nProchaine vérification dans {interval} secondes...")
            time.sleep(interval)

        except mariadb.Error as e:
            print(f"Erreur lors de la récupération : {e}")
            time.sleep(interval)

        except Exception as e:
            print(f"Erreur inattendue : {e}")
            time.sleep(interval)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage : python3 serveur_master.py <DB_IP> <MASTER_PORT>")
        sys.exit(1)

    db_ip = sys.argv[1]
    master_port = int(sys.argv[2])

    # Tester la connexion à la base de données
    print("Test de connexion à la base de données...")
    test_conn = get_db_connection(db_ip)
    if test_conn:
        print("Connexion à la base de données réussie\n")
        test_conn.close()
    else:
        print("Impossible de se connecter à la base de données")
        sys.exit(1)

    # Lancer la surveillance des routeurs dans un thread séparé
    monitor_thread = threading.Thread(
        target=monitor_routeurs, 
        args=(db_ip, 60), 
        daemon=True
    )
    monitor_thread.start()

    # Lancer le serveur master
    master(db_ip, master_port)
