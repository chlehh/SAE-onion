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

# Chiffrement du message avec la clé publique
def chiffrer(message, public_key):
    """Chiffre un message avec la clé publique."""
    # Convertir le message en entier, puis appliquer le chiffrement simple
    message_bytes = message.encode("utf-8")
    message_int = int.from_bytes(message_bytes, byteorder='big')
    return message_int * public_key

# Déchiffrement du message avec la clé privée
def dechiffrer(message_int, private_key):
    """Déchiffre un message avec la clé privée."""
    # Appliquer l'inverse du chiffrement avec la clé privée
    decrypted_message_int = message_int // private_key
    message_bytes = decrypted_message_int.to_bytes((decrypted_message_int.bit_length() + 7) // 8, byteorder='big')
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

def envoie_donne_db(nom, ip, port, type_objet, db_ip):
    """Envoie les informations du routeur à la base de données du master."""
    try:
        conn = mariadb.connect(
            host=db_ip,
            user="toto",
            password="toto",
            database="table_routage"
        )
        cur = conn.cursor()
        query = """
        INSERT INTO routeurs (nom, adresse_ip, port, type)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            adresse_ip = VALUES(adresse_ip),
            port = VALUES(port),
            type = VALUES(type)
        """
        cur.execute(query, (nom, ip, port, type_objet))
        conn.commit()
        conn.close()
        print(f"Données envoyées à la base de données pour {nom}.")
    except mariadb.Error as e:
        print(f"Erreur lors de l'envoi des données dans la DB : {e}")

def envoyer(ip, port, message):
    """Envoie un message à un autre routeur ou client de manière asynchrone."""
    try:
        s = socket.socket()
        s.connect((ip, port))
        s.send(message.encode())
        s.close()
    except socket.error as e:
        print(f"Erreur lors de l'envoi du message à {ip}:{port}: {e}")

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
            envoyer(nip, nport, rest)
            print(f"{nom} → a transmis à {next_hop}")

        # Si le prochain hop est un client
        elif next_hop in CLIENTS:
            nip, nport, cle_publique, next_hop_bdd = CLIENTS[next_hop]
            envoyer(nip, nport, rest)
            print(f"{nom} → message final envoyé au client !")
        else:
            print(f"{nom} : Next hop inconnu :", next_hop)
    except Exception as e:
        print(f"Erreur lors du traitement du message : {e}")

def routeur(nom, port, db_ip):
    """Fonction principale du routeur"""
    enregistrer_routeur(nom, port, db_ip)
    t = threading.Thread(target=traitement_message, args=(nom, "0.0.0.0", port))
    t.start()

def get_ip():
    """Retourne l'IP locale de la machine"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))  # Connexion vers Google pour déterminer l'IP sans envoyer de paquet
    ip = s.getsockname()[0]
    s.close()
    return ip

def enregistrer_routeur(nom, port, db_ip):
    """Enregistrer le routeur dans la base de données"""
    ip_locale = get_ip()
    envoie_donne_db(nom, ip_locale, port, "routeur", db_ip)
    recup_routeurs_client(db_ip)

if __name__ == "__main__":
    # Vérification des arguments
    if len(sys.argv) != 4:
        print("Utilisation : python3 routeur.py <NOM_ROUTEUR> <PORT> <DB_IP>")
        sys.exit(1)

    nom_routeur = sys.argv[1]  # Nom du routeur
    port_routeur = int(sys.argv[2])  # Port du routeur
    db_ip = sys.argv[3]  # IP de la base de données

    routeur(nom_routeur, port_routeur, db_ip)
