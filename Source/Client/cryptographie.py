#!/usr/bin/env python3
"""
cryptographie.py
Module de chiffrement RSA simplifie pour le routage en oignon
"""

import random

def pgcd(a, b):
    """Calcule le PGCD."""
    while b:
        a, b = b, a % b
    return a

def est_premier_simple(n):
    """Test de primalite simple et rapide."""
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    
    # Tester les diviseurs jusqu'a la racine carree
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True

def generer_nombre_premier(min_val=100, max_val=500):
    """Genere un nombre premier aleatoire."""
    tentatives = 0
    while tentatives < 1000:
        candidat = random.randint(min_val, max_val)
        if candidat % 2 == 0:
            candidat += 1
        if est_premier_simple(candidat):
            return candidat
        tentatives += 1
    
    # Si echec, retourner un premier connu
    premiers_connus = [101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 
                       151, 157, 163, 167, 173, 179, 181, 191, 193, 197,
                       199, 211, 223, 227, 229, 233, 239, 241, 251, 257]
    return random.choice(premiers_connus)

def inverse_modulaire(e, phi):
    """Calcule l'inverse modulaire avec l'algorithme d'Euclide etendu."""
    t, new_t = 0, 1
    r, new_r = phi, e
    
    while new_r != 0:
        quotient = r // new_r
        t, new_t = new_t, t - quotient * new_t
        r, new_r = new_r, r - quotient * new_r
    
    if r > 1:
        raise ValueError("e n'est pas inversible")
    if t < 0:
        t = t + phi
    
    return t

def generer_cles():
    """
    Genere une paire de cles RSA.
    Retourne: (cle_privee, cle_publique) sous forme ((d, n), (e, n))
    """
    p = generer_nombre_premier(100, 500)
    q = generer_nombre_premier(100, 500)
    
    while q == p:
        q = generer_nombre_premier(100, 500)
    
    n = p * q
    phi = (p - 1) * (q - 1)
    
    # Choisir e (exposant public)
    e = 65537
    if e >= phi or pgcd(e, phi) != 1:
        e = 3
        while pgcd(e, phi) != 1:
            e += 2
    
    # Calculer d (exposant prive)
    d = inverse_modulaire(e, phi)
    
    # Retourner (cle_privee, cle_publique)
    return (d, n), (e, n)

def chiffrer(message, cle_publique):
    """
    Chiffre un message avec RSA.
    message: str
    cle_publique: tuple (e, n)
    Retourne: str (nombres separes par des virgules)
    """
    e, n = cle_publique
    octets = message.encode("utf-8")
    octets_chiffres = []
    
    for octet in octets:
        chiffre = pow(octet, e, n)
        octets_chiffres.append(str(chiffre))
    
    return ",".join(octets_chiffres)

def dechiffrer(message_chiffre, cle_privee):
    """
    Dechiffre un message avec RSA.
    message_chiffre: str (nombres separes par des virgules)
    cle_privee: tuple (d, n)
    Retourne: str ou None en cas d'erreur
    """
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
    """
    Encode une cle publique pour l'envoi au Master.
    cle_publique: tuple (e, n)
    Retourne: str au format "e,n"
    """
    e, n = cle_publique
    return f"{e},{n}"

def decoder_cle_recue(cle_str):
    """
    Decode une cle publique recue du Master.
    cle_str: str au format "e,n"
    Retourne: tuple (e, n) ou None en cas d'erreur
    """
    try:
        # Nettoyer la chaine (enlever espaces, retours ligne, etc.)
        cle_str = cle_str.strip()
        
        # Separer par virgule
        parties = cle_str.split(",")
        if len(parties) != 2:
            print(f"Erreur: format invalide, {len(parties)} parties au lieu de 2")
            print(f"Contenu recu: '{cle_str}'")
            return None
        
        # Convertir en entiers
        e = int(parties[0].strip())
        n = int(parties[1].strip())
        
        print(f"Cle decodee: e={e}, n={n}")
        return (e, n)
    except Exception as ex:
        print(f"Erreur decodage cle: {ex}")
        print(f"Contenu recu: '{cle_str}'")
        import traceback
        traceback.print_exc()
        return None


