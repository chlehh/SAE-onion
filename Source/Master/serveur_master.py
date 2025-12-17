import socket
import random
import mariadb
import sys

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
    return socket.gethostbyname(socket.gethostname())

def master(db_ip, master_port):
    """Serveur Master qui gère la demande de chemin"""
    host = "0.0.0.0"  # Écoute sur toutes les interfaces
    port = master_port

    server = socket.socket()
    server.bind((host, port))
    server.listen(5)

    ip_master = get_ip_locale()  # IP dynamique du Master
    print(f"MASTER en écoute sur {ip_master}:{port}...")

    while True:
        conn, addr = server.accept()
        print("Client connecté :", addr)

        data = conn.recv(1024).decode()
        print("Reçu du client :", data)

        parts = data.split()

        nom_client = parts[0]  # Nom du client (par exemple "CLIENT1")
        nb_sauts = int(parts[1])  # Nombre de sauts choisi par le client
        routeurs_choisis = parts[2:]  # Liste des routeurs choisis par le client

        print(f"Client {nom_client} a choisi {nb_sauts} sauts avec les routeurs : {routeurs_choisis}")

        chemin = generer_chemin(nb_sauts, routeurs_choisis)
        chemin_str = ",".join(chemin)

        # Enregistrer un log
        message_id = f"{nom_client}-{nb_sauts}-{chemin_str}"
        enregistrer_log(message_id, "MASTER", db_ip)

        conn.send(chemin_str.encode())
        print(f"Chemin envoyé :", chemin_str)

        conn.close()

def get_db_ip():
    """Récupère l'IP du serveur MariaDB depuis la ligne de commande"""
    if len(sys.argv) < 3:
        print("Erreur : Vous devez spécifier l'IP de la base de données et le port du Master.")
        sys.exit(1)
    return sys.argv[1]

def get_master_port():
    """Récupère le port du serveur Master depuis la ligne de commande"""
    return int(sys.argv[2])

if __name__ == "__main__":
    db_ip = get_db_ip()  # IP de la base de données
    master_port = get_master_port()  # Port du serveur Master

    recup_routeurs(db_ip)  # Récupérer les routeurs depuis la base de données
    master(db_ip, master_port)
