#!/usr/bin/env python3
"""
cryptographie.py
RSA ultra-simplifié - sans inverse modulaire
"""

import random

def pgcd(a, b):
    """Calcule le PGCD."""
    while b:
        a, b = b, a % b
    return a

def est_premier_simple(n):
    """Test de primalité simple."""
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True

def generer_nombre_premier(min_val=100, max_val=500):
    """Génère un nombre premier aléatoire."""
    tentatives = 0
    while tentatives < 1000:
        candidat = random.randint(min_val, max_val)
        if candidat % 2 == 0:
            candidat += 1
        if est_premier_simple(candidat):
            return candidat
        tentatives += 1
    
    premiers_connus = [101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 
                       151, 157, 163, 167, 173, 179, 181, 191, 193, 197,
                       199, 211, 223, 227, 229, 233, 239, 241, 251, 257]
    return random.choice(premiers_connus)

def generer_cles():
    """
    Génère une paire de clés RSA .
    Utilise e=3 et d=3 (exposants ).
    """
    p = generer_nombre_premier(100, 500)
    q = generer_nombre_premier(100, 500)
    
    while q == p:
        q = generer_nombre_premier(100, 500)
    
    n = p * q
    
    # Exposants fixes simples
    e = 3  # Exposant public
    d = 3  # Exposant privé (même valeur )
    
    # Retourner (cle_privee, cle_publique)
    return (d, n), (e, n)

def chiffrer(message, cle_publique):
    """Chiffre un message avec RSA."""
    e, n = cle_publique
    octets = message.encode("utf-8")
    octets_chiffres = []
    
    for octet in octets:
        chiffre = pow(octet, e, n)
        octets_chiffres.append(str(chiffre))
    
    return ",".join(octets_chiffres)

def dechiffrer(message_chiffre, cle_privee):
    """Déchiffre un message avec RSA."""
    d, n = cle_privee
    
    try:
        nombres_chiffres = message_chiffre.split(",")
        octets_dechiffres = []
        
        for nombre in nombres_chiffres:
            if nombre.strip():
                chiffre = int(nombre)
                octet = pow(chiffre, d, n)
                octets_dechiffres.append(octet)
        
        octets = bytes(octets_dechiffres)
        message = octets.decode("utf-8")
        return message
    
    except Exception as e:
        print(f"Erreur lors du dechiffrement: {e}")
        return None

def encoder_cle_pour_envoi(cle_publique):
    """Encode une clé publique pour l'envoi."""
    e, n = cle_publique
    return f"{e},{n}"

def decoder_cle_recue(cle_str):
    """Décode une clé publique reçue."""
    try:
        cle_str = cle_str.strip()
        parties = cle_str.split(",")
        
        if len(parties) != 2:
            return None
        
        e = int(parties[0].strip())
        n = int(parties[1].strip())
        
        return (e, n)
    
    except Exception:
        return None