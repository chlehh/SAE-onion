import socket
import threading

# Fonction pour gérer les connexions des clients
def handle_client(client_socket):
    request = client_socket.recv(1024)  # Recevoir les données du client
    print(f"Reçu du client : {request.decode('utf-8')}")
    
    # Réponse du serveur maître
    client_socket.send(b"Réponse du serveur maître")
    client_socket.close()

# Fonction principale du serveur
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5555))  # Écoute sur toutes les interfaces et le port 5555
    server.listen(5)  # Nombre de connexions en attente

    print("Serveur maître en écoute sur le port 5555...")
    
    while True:
        client_socket, addr = server.accept()  # Accepter la connexion du client
        print(f"Connexion de {addr}")
        
        # Créer un thread pour chaque connexion
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

# Démarrer le serveur maître
if __name__ == "__main__":
    start_server()
