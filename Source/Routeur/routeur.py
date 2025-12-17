import socket
import mariadb
import sys

def routeur(master_ip, master_port, routeur_port, db_ip):
    """Démarre un routeur et reçoit les messages chiffrés"""
    print(f"Routeur démarré sur le port {routeur_port}")
    
    # Connexion au serveur Master pour récupérer les informations nécessaires
    chemin = demander_chemin_au_master(master_ip, master_port)
    print(f"Chemin reçu du Master : {chemin}")

    # Démarre l'écoute sur le port spécifié pour le routeur
    server = socket.socket()
    server.bind(("0.0.0.0", routeur_port))
    server.listen(5)

    print(f"Routeur en écoute sur {routeur_port}...")

    while True:
        conn, addr = server.accept()
        print(f"Message reçu de {addr}")
        data = conn.recv(1024).decode()

        print(f"Message reçu : {data}")

        # Déchiffrement de la couche du message
        next_hop, message_rest = data.split("|", 1)

        # Si le prochain hop est un autre routeur, on transmet le message
        if next_hop in chemin:
            ip, port = get_routeur_ip_and_port(next_hop, db_ip)
            envoyer(ip, port, message_rest)

        # Si c'est un client, on envoie le message final
        else:
            print(f"Message final envoyé au client {next_hop}: {message_rest}")

        conn.close()

def demander_chemin_au_master(master_ip, master_port):
    """Demande un chemin au serveur Master"""
    s = socket.socket()
    s.connect((master_ip, master_port))

    message = "Routeur GET_PATH 3"  # Exemple pour 3 sauts
    s.send(message.encode())

    chemin = s.recv(1024).decode().split(",")
    s.close()

    return chemin

def get_routeur_ip_and_port(routeur, db_ip):
    """Récupère l'IP et le port du routeur depuis la base de données"""
    try:
        conn = mariadb.connect(
            host=db_ip,
            user="toto",
            password="toto",
            database="table_routage"
        )
        cur = conn.cursor()

        # Rechercher les informations du routeur
        cur.execute("SELECT adresse_ip, port FROM routeurs WHERE nom = %s", (routeur,))
        row = cur.fetchone()

        conn.close()

        if row:
            return row
        else:
            print(f"Erreur : Routeur {routeur} non trouvé dans la base de données.")
            sys.exit(1)

    except mariadb.Error as e:
        print(f"Erreur lors de la récupération des données de la DB : {e}")
        sys.exit(1)

def envoyer(ip, port, message):
    """Envoie le message au prochain routeur ou client"""
    s = socket.socket()
    s.connect((ip, port))
    s.send(message.encode())
    s.close()

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage : python routeur.py -m <MASTER_IP>:<MASTER_PORT> -p <ROUTEUR_PORT> -d <DB_IP>")
        sys.exit(1)

    master_ip, master_port = sys.argv[2].split(":")
    master_port = int(master_port)
    routeur_port = int(sys.argv[4])
    db_ip = sys.argv[6]

    routeur(master_ip, master_port, routeur_port, db_ip)
