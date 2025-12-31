#!/usr/bin/env python3
"""Serveur Master"""

import socket
import mariadb
import threading

def get_db_connection(db_ip):
    """Connexion à la base de données"""
    try:
        return mariadb.connect(
            host=db_ip,
            user="toto",
            password="toto",
            database="table_routage"
        )
    except mariadb.Error as e:
        print(f"Erreur DB: {e}")
        return None

def enregistrer_routeur(nom, ip, port, cle_pub, db_ip):
    """Enregistre un routeur"""
    conn = get_db_connection(db_ip)
    if not conn:
        return False
    
    cur = conn.cursor()
    cur.execute("SELECT id FROM routeurs WHERE nom = %s", (nom,))
    
    if cur.fetchone():
        # Mise à jour
        cur.execute("""UPDATE routeurs 
                      SET adresse_ip=%s, port=%s, cle_publique=%s 
                      WHERE nom=%s""", 
                   (ip, port, cle_pub, nom))
    else:
        # Insertion
        cur.execute("""INSERT INTO routeurs (nom, adresse_ip, port, type, cle_publique)
                      VALUES (%s, %s, %s, 'routeur', %s)""",
                   (nom, ip, port, cle_pub))
    
    conn.commit()
    conn.close()
    print(f" Routeur {nom} enregistré")
    return True

def enregistrer_client(nom, ip, port, db_ip):
    """Enregistre un client"""
    conn = get_db_connection(db_ip)
    if not conn:
        return False
    
    cur = conn.cursor()
    cur.execute("SELECT id FROM clients WHERE nom = %s", (nom,))
    
    if cur.fetchone():
        cur.execute("UPDATE clients SET adresse_ip=%s, port=%s WHERE nom=%s",
                   (ip, port, nom))
    else:
        cur.execute("INSERT INTO clients (nom, adresse_ip, port) VALUES (%s, %s, %s)",
                   (nom, ip, port))
    
    conn.commit()
    conn.close()
    print(f" Client {nom} enregistré")
    return True

def recup_routeurs(db_ip):
    """Récupère la liste des routeurs"""
    conn = get_db_connection(db_ip)
    if not conn:
        return {}
    
    cur = conn.cursor()
    cur.execute("SELECT nom, adresse_ip, port, cle_publique FROM routeurs WHERE type='routeur'")
    
    routeurs = {}
    for nom, ip, port, cle in cur.fetchall():
        routeurs[nom] = {"ip": ip, "port": port, "cle_publique": cle or ""}
    
    conn.close()
    return routeurs

def recup_clients(db_ip):
    """Récupère la liste des clients"""
    conn = get_db_connection(db_ip)
    if not conn:
        return {}
    
    cur = conn.cursor()
    cur.execute("SELECT nom, adresse_ip, port FROM clients")
    
    clients = {}
    for nom, ip, port in cur.fetchall():
        clients[nom] = {"ip": ip, "port": port}
    
    conn.close()
    return clients

def handle_client_connection(conn, addr, db_ip):
    """Gère une connexion entrante"""
    try:
        data = conn.recv(4096).decode()
        print(f"Reçu de {addr}: {data}")
        
        if data.startswith("Routeur"):
            # Format: "Routeur <nom> <port> <cle_publique>"
            parts = data.split(maxsplit=3)
            if len(parts) >= 4:
                nom, port, cle = parts[1], int(parts[2]), parts[3]
                success = enregistrer_routeur(nom, addr[0], port, cle, db_ip)
                conn.send(("OK" if success else "ERROR").encode())
        
        elif data.startswith("Client"):
            # Format: "Client <nom> <port>"
            parts = data.split()
            if len(parts) >= 3:
                nom, port = parts[1], int(parts[2])
                success = enregistrer_client(nom, addr[0], port, db_ip)
                conn.send(("OK" if success else "ERROR").encode())
        
        elif data == "GET_ALL":
            routeurs = recup_routeurs(db_ip)
            clients = recup_clients(db_ip)
            
            routeurs_str = ";".join([f"{n}:{i['ip']}:{i['port']}:{i['cle_publique']}" 
                                    for n, i in routeurs.items()])
            clients_str = ";".join([f"{n}:{i['ip']}:{i['port']}" 
                                   for n, i in clients.items()])
            
            response = f"ROUTEURS:{routeurs_str}|CLIENTS:{clients_str}"
            conn.send(response.encode())
        
        elif data.startswith("GET_INFO:"):
            nom = data.split(":", 1)[1]
            routeurs = recup_routeurs(db_ip)
            clients = recup_clients(db_ip)
            
            if nom in routeurs:
                info = routeurs[nom]
                conn.send(f"{info['ip']}:{info['port']}".encode())
            elif nom in clients:
                info = clients[nom]
                conn.send(f"{info['ip']}:{info['port']}".encode())
            else:
                conn.send("ERROR".encode())
        
        else:
            conn.send("ERROR".encode())
    
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        conn.close()

def master(db_ip, master_port):
    """Lance le serveur Master"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", master_port))
    server.listen(5)
    
    print(f" Master en écoute sur port {master_port}\n")
    
    while True:
        try:
            conn, addr = server.accept()
            thread = threading.Thread(
                target=handle_client_connection,
                args=(conn, addr, db_ip),
                daemon=True
            )
            thread.start()
        except KeyboardInterrupt:
            break
    
    server.close()

def check_routeur_status(ip, port):
    """Vérifie si un routeur est en ligne"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((ip, port))
        s.close()
        return True
    except:
        return False

def check_client_status(ip, port):
    """Vérifie si un client est en ligne"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((ip, port))
        s.close()
        return True
    except:
        return False

def remove_inactive_routeur(nom, db_ip):
    """Supprime un routeur inactif"""
    conn = get_db_connection(db_ip)
    if not conn:
        return False
    
    cur = conn.cursor()
    cur.execute("DELETE FROM routeurs WHERE nom = %s", (nom,))
    conn.commit()
    conn.close()
    print(f"✗ Routeur {nom} supprimé (inactif)")
    return True

def remove_inactive_client(nom, db_ip):
    """Supprime un client inactif"""
    conn = get_db_connection(db_ip)
    if not conn:
        return False
    
    cur = conn.cursor()
    cur.execute("DELETE FROM clients WHERE nom = %s", (nom,))
    conn.commit()
    conn.close()
    print(f"✗ Client {nom} supprimé (inactif)")
    return True

def monitor_routeurs(db_ip, interval=60):
    """Surveille les routeurs et clients actifs"""
    import time
    
    while True:
        try:
            print("\n=== Vérification des connexions ===")
            conn = get_db_connection(db_ip)
            if not conn:
                time.sleep(interval)
                continue
            
            cur = conn.cursor()
            
            # Vérifier routeurs
            cur.execute("SELECT nom, adresse_ip, port FROM routeurs WHERE type = 'routeur'")
            routeurs = cur.fetchall()
            
            # Vérifier clients
            cur.execute("SELECT nom, adresse_ip, port FROM clients")
            clients = cur.fetchall()
            
            conn.close()
            
            # Tester routeurs
            for nom, ip, port in routeurs:
                if not check_routeur_status(ip, port):
                    print(f"   {nom} inactif")
                    remove_inactive_routeur(nom, db_ip)
                else:
                    print(f"   {nom} actif")
            
            # Tester clients
            for nom, ip, port in clients:
                if not check_client_status(ip, port):
                    print(f"   {nom} inactif")
                    remove_inactive_client(nom, db_ip)
                else:
                    print(f"   {nom} actif")
            
            print(f"\nProchaine vérification dans {interval}s...")
            time.sleep(interval)
        
        except Exception as e:
            print(f"Erreur monitoring: {e}")
            time.sleep(interval)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python serveur_master.py <DB_IP> <PORT>")
        sys.exit(1)
    
    db_ip = sys.argv[1]
    port = int(sys.argv[2])
    
    # Lancer monitoring dans un thread séparé
    monitor_thread = threading.Thread(
        target=monitor_routeurs,
        args=(db_ip, 60),
        daemon=True
    )
    monitor_thread.start()
    
    # Lancer le serveur
    master(db_ip, port)