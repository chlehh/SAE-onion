import socket
import mariadb
import sys
import time

ROUTEURS = {}
CLIENTS = {}

def check_routeur_status(routeur_ip, routeur_port):
    """Vérifie si un routeur est toujours en ligne."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)  # Timeout de 2 secondes pour la connexion
        s.connect((routeur_ip, routeur_port))
        s.close()
        print(f"Routeur {routeur_ip}:{routeur_port} est actif.")
        return True
    except (socket.error, socket.timeout):
        print(f"Routeur {routeur_ip}:{routeur_port} est inactif.")
        return False

def remove_inactive_routeur(routeur_nom, db_ip):
    """Supprime un routeur inactif de la base de données."""
    try:
        print(f"Tentative de suppression du routeur {routeur_nom} de la base de données...")
        conn = mariadb.connect(
            host=db_ip,
            user="toto",
            password="toto",
            database="table_routage"
        )
        cur = conn.cursor()
        cur.execute("DELETE FROM routeurs WHERE nom = %s", (routeur_nom,))
        conn.commit()
        conn.close()
        print(f"Routeur {routeur_nom} supprimé de la base de données.")
    except mariadb.Error as e:
        print(f"Erreur lors de la suppression du routeur de la DB : {e}")

def remove_inactive_client(client_nom, db_ip):
    """Supprime un client inactif de la base de données."""
    try:
        print(f"Tentative de suppression du client {client_nom} de la base de données...")
        conn = mariadb.connect(
            host=db_ip,
            user="toto",
            password="toto",
            database="table_routage"
        )
        cur = conn.cursor()
        cur.execute("DELETE FROM routeurs WHERE nom = %s AND type = 'client'", (client_nom,))
        conn.commit()
        conn.close()
        print(f"Client {client_nom} supprimé de la base de données.")
    except mariadb.Error as e:
        print(f"Erreur lors de la suppression du client de la DB : {e}")

def recup_routeurs(db_ip):
    """Récupère les informations des routeurs depuis la base de données"""
    try:
        conn = mariadb.connect(
            host=db_ip,
            user="toto",
            password="toto",
            database="table_routage"
        )
        cur = conn.cursor()
        cur.execute("SELECT nom, adresse_ip, port, cle_publique FROM routeurs WHERE type='routeur'")
        rows_routeurs = cur.fetchall()
        conn.close()

        routeurs = {}
        for nom, ip, port, cle_publique in rows_routeurs:
            routeurs[nom] = {"ip": ip, "port": port, "cle_publique": cle_publique}

        return routeurs

    except mariadb.Error as e:
        print(f"Erreur lors de la récupération des données de la DB : {e}")
        sys.exit(1)

def enregistrer_routeur(nom, ip, port, cle_publique, db_ip):
    """Enregistre un routeur dans la base de données"""
    try:
        conn = mariadb.connect(
            host=db_ip,
            user="toto",
            password="toto",
            database="table_routage"
        )
        cur = conn.cursor()
        cur.execute("INSERT INTO routeurs (nom, adresse_ip, port, cle_publique, type) VALUES (%s, %s, %s, %s, 'routeur')", 
                    (nom, ip, port, cle_publique))
        conn.commit()
        conn.close()
        print(f"Routeur {nom} enregistré dans la base de données.")
    
    except mariadb.Error as e:
        print(f"Erreur lors de l'enregistrement du routeur dans la DB : {e}")
        sys.exit(1)

def enregistrer_log(message_id, routeur, db_ip):
    """Enregistre les logs dans la base de données"""
    try:
        conn = mariadb.connect(
            host=db_ip,
            user="toto",
            password="toto",
            database="table_routage"
        )
        cur = conn.cursor()
        cur.execute("INSERT INTO logs (message_id, routeur) VALUES (%s, %s)", (message_id, routeur))
        conn.commit()
        conn.close()
        print(f"Log enregistré pour le message {message_id}")
    except mariadb.Error as e:
        print(f"Erreur lors de l'enregistrement des logs : {e}")
        sys.exit(1)

def master(db_ip, master_port):
    """Serveur Master qui gère la demande des clients pour récupérer la liste des routeurs"""
    host = "0.0.0.0"  # Écoute sur toutes les interfaces
    port = master_port

    print(f"MASTER en écoute sur {host}:{port}...")

    server = socket.socket()
    try:
        server.bind((host, port))
        server.listen(5)
    except socket.error as e:
        print(f"Erreur lors de l'ouverture du port {port}: {e}")
        sys.exit(1)

    while True:
        try:
            conn, addr = server.accept()
            print(f"Client connecté : {addr}")

            # Envoyer l'IP de la base de données au client
            conn.send(db_ip.encode())  # Envoyer l'IP de la base de données

            data = conn.recv(1024).decode()
            print("Reçu du client :", data)

            if data.startswith("Routeur"):
                # Enregistrement du routeur
                parts = data.split()
                nom_routeur = parts[1]
                ip_routeur = addr[0]
                port_routeur = int(parts[2])
                cle_publique = parts[3]

                enregistrer_routeur(nom_routeur, ip_routeur, port_routeur, cle_publique, db_ip)

            elif data.startswith("Client"):
                # Enregistrement du client
                parts = data.split()
                nom_client = parts[1]
                ip_client = addr[0]
                port_client = int(parts[2])

                enregistrer_client(nom_client, ip_client, port_client, db_ip)

            elif data == "GET_ROUTEURS":
                routeurs = recup_routeurs(db_ip)
                conn.send(str(routeurs).encode())
                print(f"Liste des routeurs envoyée au client {addr}")

            conn.close()

        except socket.error as e:
            print(f"Erreur de connexion avec le client : {e}")

def monitor_routeurs(db_ip, interval=60):
    """Surveille les routeurs actifs et supprime ceux qui sont inactifs."""
    while True:
        try:
            print("Vérification des routeurs...")
            conn = mariadb.connect(
                host=db_ip,
                user="toto",
                password="toto",
                database="table_routage"
            )
            cur = conn.cursor()
            cur.execute("SELECT nom, adresse_ip, port FROM routeurs WHERE type = 'routeur'")
            routeurs = cur.fetchall()
            conn.close()

            for routeur in routeurs:
                nom, ip, port = routeur
                print(f"Vérification du routeur {nom} - {ip}:{port}")
                if not check_routeur_status(ip, port):  # Si le routeur est inactif
                    print(f"{nom} est inactif. Suppression de la base de données.")
                    remove_inactive_routeur(nom, db_ip)

            print(f"Attente de {interval} secondes avant la prochaine vérification...")
            time.sleep(interval)

        except mariadb.Error as e:
            print(f"Erreur lors de la récupération des routeurs de la DB : {e}")
            time.sleep(interval)  # Attendre avant de réessayer en cas d'erreur avec la DB

        except Exception as e:
            print(f"Erreur inattendue : {e}")
            time.sleep(interval)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage : python3 serveur_master.py <DB_IP> <MASTER_PORT>")
        sys.exit(1)

    db_ip = sys.argv[1]  # L'IP de la base de données récupérée en ligne de commande
    master_port = int(sys.argv[2])  # Port du serveur Master

    # Lancer le serveur master
    master(db_ip, master_port)
