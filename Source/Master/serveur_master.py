import socket
import mariadb
import sys
import random
import time

ROUTEURS = {}

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

        # Récupérer les routeurs
        cur.execute("SELECT nom, adresse_ip, port, cle_publique FROM routeurs WHERE type='routeur'")
        rows_routeurs = cur.fetchall()

        conn.close()

        global ROUTEURS
        ROUTEURS = {}
        for nom, ip, port, cle_publique in rows_routeurs:
            ROUTEURS[nom] = (ip, port, cle_publique)

        print("Routeurs récupérés:", ROUTEURS)

    except mariadb.Error as e:
        print(f"Erreur lors de la récupération des données de la DB : {e}")
        sys.exit(1)

def generer_chemin(nb_sauts, routeurs_choisis):
    """Génère un chemin en fonction du nombre de sauts et des routeurs sélectionnés"""
    if nb_sauts > len(routeurs_choisis):
        nb_sauts = len(routeurs_choisis)

    chemin = random.sample(routeurs_choisis, nb_sauts)
    return chemin

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

        # Insérer un log
        cur.execute("INSERT INTO logs (message_id, routeur) VALUES (%s, %s)", (message_id, routeur))

        conn.commit()
        conn.close()

        print(f"Log enregistré pour le message {message_id}")

    except mariadb.Error as e:
        print(f"Erreur lors de l'enregistrement des logs : {e}")
        sys.exit(1)

def get_ip_locale():
    """Retourne l'IP locale de la machine"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))  # Connecte à un serveur externe pour déterminer l'IP locale
    ip = s.getsockname()[0]
    s.close()
    print(f"IP locale du serveur Master : {ip}")  # Affichage de l'IP locale
    return ip

def master(db_ip, master_port):
    """Serveur Master qui gère la demande de chemin"""
    host = "0.0.0.0"  # Écoute sur toutes les interfaces
    port = master_port

    ip_master = get_ip_locale()  # IP dynamique du Master
    print(f"MASTER en écoute sur {ip_master}:{port}...")

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

            data = conn.recv(1024).decode()
            print("Reçu du client :", data)

            # Si un routeur demande l'IP de la base de données, on lui renvoie
            if data == "Routeur GET_DB_IP":
                conn.send(db_ip.encode())  # Envoie l'IP de la base de données
                print(f"IP de la base de données envoyée : {db_ip}")
                conn.close()
                continue

            parts = data.split()

            nom_client = parts[0]  # Nom du client (par exemple "CLIENT1")

            # Vérifier si la commande est correcte (GET_PATH)
            if len(parts) < 3:
                print(f"Erreur : La commande est mal formée.")
                conn.send("Erreur : Commande mal formée.".encode())
                conn.close()
                continue

            if parts[1] == "GET_PATH":
                try:
                    nb_sauts = int(parts[2])  # Le nombre de sauts est dans parts[2]
                except ValueError:
                    print(f"Erreur : Le nombre de sauts n'est pas valide.")
                    conn.send(b"Erreur : Nombre de sauts invalide.")
                    conn.close()
                    continue
            else:
                print(f"Erreur : Commande inconnue reçue ({data})")
                conn.send(b"Erreur : Commande inconnue.")
                conn.close()
                continue

            routeurs_choisis = parts[3:]  # Liste des routeurs choisis par le client

            print(f"Client {nom_client} a choisi {nb_sauts} sauts avec les routeurs : {routeurs_choisis}")

            chemin = generer_chemin(nb_sauts, routeurs_choisis)
            chemin_str = ",".join(chemin)

            # Enregistrer un log
            message_id = f"{nom_client}-{nb_sauts}-{chemin_str}"
            enregistrer_log(message_id, "MASTER", db_ip)

            conn.send(chemin_str.encode())
            print(f"Chemin envoyé :", chemin_str)

            conn.close()

        except socket.error as e:
            print(f"Erreur de connexion avec le client : {e}")

if __name__ == "__main__":
    # L'IP de la base de données et le port du serveur Master sont fournis via la ligne de commande
    if len(sys.argv) < 3:
        print("Usage : python serveur_master.py <DB_IP> <MASTER_PORT>")
        sys.exit(1)

    db_ip = sys.argv[1]  # IP de la base de données
    master_port = int(sys.argv[2])  # Port du serveur Master

    recup_routeurs(db_ip)  # Récupérer les routeurs depuis la base de données
    master(db_ip, master_port)  # Démarrer le serveur Master
