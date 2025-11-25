import socket
import threading

# Fonction pour envoyer un message au serveur
def send_message(client_socket):
    message = "Message du client"
    client_socket.send(message.encode())  # Envoi du message
    response = client_socket.recv(1024)  # Attente de la réponse
    print(f"Réponse du serveur : {response.decode('utf-8')}")
    client_socket.close()

# Fonction principale du client
def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 5555))  # Connexion au serveur maître
    
    # Envoyer un message de manière asynchrone
    send_message(client)

# Démarrer le client dans un thread
if __name__ == "__main__":
    client_thread = threading.Thread(target=start_client)
    client_thread.start()
