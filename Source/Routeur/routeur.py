import socket
import threading

# Fonction pour gérer les connexions du routeur
def handle_router(client_socket):
    data = client_socket.recv(1024)  # Recevoir le message
    print(f"Message reçu par le routeur : {data.decode('utf-8')}")
    
    # Traitement du message (par exemple, déchiffrer une couche)
    client_socket.send(b"Message traité par le routeur")
    client_socket.close()

# Fonction principale pour démarrer le routeur
def start_router():
    router = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    router.bind(("0.0.0.0", 5556))  # Port pour ce routeur
    router.listen(5)  # Nombre de connexions en attente

    print("Routeur en écoute sur le port 5556...")

    while True:
        client_socket, addr = router.accept()  # Accepter une connexion
        print(f"Connexion du client {addr}")
        
        # Créer un thread pour chaque connexion
        router_handler = threading.Thread(target=handle_router, args=(client_socket,))
        router_handler.start()

# Démarrer le routeur
if __name__ == "__main__":
    start_router()
