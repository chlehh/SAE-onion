import socket
import mariadb
import threading
import random
import sys
import time

ROUTEURS = {}
CLIENTS = {}

# Générer une clé privée et une clé publique aléatoires
def generer_cle():
    """Génère une clé privée et une clé publique."""
    private_key = random.getrandbits(256)  # Clé privée aléatoire (256 bits)
    public_key = private_key * random.getrandbits(256)  # Clé publique dérivée de la clé privée
    return private_key, public_key

# Chiffrement du message avec plusieurs couches (pour chaque routeur)
def chiffrer(message, routeurs):
    """Chiffre un message avec plusieurs couches, une pour chaque routeur."""
    message_bytes = message.encode("utf-8")
    message_int = int.from_bytes(message_bytes, byteorder='big')

    # Appliquer plusieurs couches de chiffrement, chaque routeur ayant sa propre clé publique
    for routeur in routeurs:
        public_key = routeur['cle_publique']
        message_int = message_int * public_key  # Chiffrement avec la clé publique du routeur

    return message_int

# Déchiffrement du message avec plusieurs couches (pour chaque routeur)
def dechiffrer(message_int, routeurs):
    """Déchiffre un message avec plusieurs couches de déchiffrement."""
    for routeur in reversed(routeurs):  # On commence par le dernier routeur
        private_key = routeur['cle_privee']
        message_int = message_int // private_key  # Déchiffrement avec la clé privée du routeur

    # Convertir l'entier déchiffré en bytes et le décoder en texte
    message_bytes = message_int.to_bytes((message_int.bit_length() + 7) // 8, byteorder='big')
    return message_bytes.decode("utf-8")

def recup_routeurs_client(db_ip):
    """Récupère les informations des routeurs et des clients de la base de données."""
    global ROUTEURS, CLIENTS
    try:
        conn = mariadb.connect(
            host=db_ip,  # IP de la base de données passée en paramètre
            user="toto",
            password="toto",
            database="table_routage"
        )
        cur = conn.cursor()

        # Récupérer les informations des routeurs
        cur.execute("SELECT nom, adresse_ip, port, cle_publique, next_hop FROM routeurs WHERE type='routeur'")
        rows_routeurs = cur.fetchall()

        # Récupérer les informations des clients
        cur.execute("SELECT nom, adresse_ip, port, cle_publique, next_hop FROM routeurs WHERE type='client'")
        rows_clients = cur.fetchall()

        conn.close()

        # Remplir le dictionnaire des routeurs
        ROUTEURS = {}
        for nom, ip, port, cle_publique, next_hop in rows_routeurs:
            ROUTEURS[nom] = {"ip": ip, "port": port, "cle_publique": cle_publique, "next_hop": next_hop}

        # Remplir le dictionnaire des clients
        CLIENTS = {}
        for nom, ip, port, cle_publique, next_hop in rows_clients:
            CLIENTS[nom] = {"ip": ip, "port": port, "cle_publique": cle_publique, "next_hop": next_hop}

    except mariadb.Error as e:
        print(f"Erreur lors de la récupération des données de la DB : {e}")
        sys.exit(1)

def envoie_donne_db(nom, ip, port, type_objet, cle_publique, db_ip):
    """Envoie les informations du routeur à la base de données du master avec la clé publique."""
    try:
        conn = mariadb.connect(
            host=db_ip,  # IP de la base de données
            user="toto",
            password="toto",
            database="table_routage"
        )
        cur = conn.cursor()

        # Enregistrement du routeur avec sa clé publique dans la base de données
        query = """
        INSERT INTO routeurs (nom, adresse_ip, port, cle_publique, type)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            adresse_ip = VALUES(adresse_ip),
            port = VALUES(port),
            cle_publique = VALUES(cle_publique),
            type = VALUES(type)
        """
        cur.execute(query, (nom, ip, port, cle_publique, type_objet))
        conn.commit()
        conn.close()
        print(f"Données envoyées à la base de données pour {nom}.")
    except mariadb.Error as e:
        print(f"Erreur lors de l'envoi des données dans la DB : {e}")
        sys.exit(1)

def envoyer(s, ip, port, message):
    """Envoie un message à un autre routeur ou client de manière persistante."""
    try:
        s.connect((ip, port))
        s.send(message.encode())
        # Garder la connexion ouverte pour envoyer plus de messages
        print(f"Message envoyé à {ip}:{port}")
    except socket.error as e:
        print(f"Erreur lors de l'envoi du message à {ip}:{port}: {e}")
        sys.exit(1)

def traitement_message(nom, message):
    """Traite le message reçu et décide du prochain hop."""
    print(f"{nom} a reçu : {message}")

    try:
        parts = message.split("|", 1)
        next_hop = parts[0]  # Next hop (routeur ou client)
        rest = parts[1]  # Le reste du message à envoyer

        # Si le prochain hop est un routeur
        if next_hop in ROUTEURS:
            nip, nport, cle_publique, next_hop_bdd = ROUTEURS[next_hop]
            with socket.socket() as s:
                envoyer(s, nip, nport, rest)
            print(f"{nom} → a transmis à {next_hop}")

        # Si le prochain hop est un client
        elif next_hop in CLIENTS:
            nip, nport, cle_publique, next_hop_bdd = CLIENTS[next_hop]
            with socket.socket() as s:
                envoyer(s, nip, nport, rest)
            print(f"{nom} → message final envoyé au client !")

        else:
            print(f"{nom} : Next hop inconnu :", next_hop)
    except Exception as e:
        print(f"Erreur lors du traitement du message : {e}")

def traitement_reception(nom, ip, port):
    """Écoute les messages reçus par le routeur et crée un thread pour chaque message."""
    print(f"{nom} écoute sur {ip}:{port}")

    s = socket.socket()
    s.bind((ip, port))
    s.listen(5)

    while True:
        conn, addr = s.accept()
        message = conn.recv(1024).decode()
        conn.close()

        # Chaque message reçu crée un nouveau thread pour le traiter
        threading.Thread(target=traitement_message, args=(nom, message)).start()

def base_de_donne(nom, port, cle_publique, db_ip):
    """Envoie les informations du routeur à la base de données."""
    ip_locale = get_ip()
    envoie_donne_db(nom, ip_locale, port, "routeur", cle_publique, db_ip)
    recup_routeurs_client(db_ip)

def routeur(nom, port, ip_master):
    """Fonction principale du routeur"""
    # Connexion au master pour récupérer l'IP de la base de données
    try:
        s = socket.socket()
        s.connect((ip_master, 5001))  # Connexion au serveur master sur le port 5001
        db_ip = s.recv(1024).decode()  # Récupération de l'IP de la base de données
        s.close()

        # Générer une clé publique et privée pour ce routeur
        private_key, public_key = generer_cle()

        # Enregistrement du routeur avec sa clé publique dans la base de données
        base_de_donne(nom, port, public_key, db_ip)

        # Démarrage du thread pour écouter les messages
        t = threading.Thread(target=traitement_reception, args=(nom, "0.0.0.0", port))
        t.start()
    except socket.error as e:
        print(f"Erreur de connexion au master : {e}")
        sys.exit(1)

def get_ip():
    """Retourne l'IP locale de la machine"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))  # Connexion vers Google pour déterminer l'IP sans envoyer de paquet
    ip = s.getsockname()[0]
    s.close()
    return ip

if __name__ == "__main__":
    # Vérification des arguments
    if len(sys.argv) != 4:
        print("Utilisation : python3 routeur.py <NOM_ROUTEUR> <PORT> <MASTER_IP>")
        sys.exit(1)

    nom_routeur = sys.argv[1]  # Nom du routeur
    port_routeur = int(sys.argv[2])  # Port du routeur
    ip_master = sys.argv[3]  # IP du serveur Master

    routeur(nom_routeur, port_routeur, ip_master)
