#!/usr/bin/env python3
"""Chiffrement RSA simplifié"""

import random
import math
from sympy import isprime

def generer_cles():
    """Génère une paire de clés RSA (clé_privée, clé_publique)"""
    # Choisir deux nombres premiers différents
    primes = [i for i in range(100, 500) if isprime(i)]
    p = random.choice(primes)
    q = random.choice([x for x in primes if x != p])
    
    n = p * q
    phi = (p - 1) * (q - 1)
    
    # Exposant public
    e = 65537 if math.gcd(65537, phi) == 1 else 3
    while math.gcd(e, phi) != 1:
        e += 2
    
    # Exposant privé (inverse modulaire)
    d = pow(e, -1, phi)
    
    return (d, n), (e, n)  # (privée, publique)

def chiffrer(message, cle_publique):
    """Chiffre un message"""
    e, n = cle_publique
    octets = message.encode("utf-8")
    chiffres = [str(pow(b, e, n)) for b in octets]
    return ",".join(chiffres)

def dechiffrer(message_chiffre, cle_privee):
    """Déchiffre un message"""
    d, n = cle_privee
    try:
        nombres = [int(x) for x in message_chiffre.split(",") if x.strip()]
        octets = bytes(pow(nb, d, n) for nb in nombres)
        return octets.decode("utf-8")
    except:
        return None

def encoder_cle_pour_envoi(cle_publique):
    """Encode clé publique en texte: 'e,n'"""
    e, n = cle_publique
    return f"{e},{n}"

def decoder_cle_recue(cle_str):
    """Décode clé publique depuis texte"""
    try:
        parties = cle_str.strip().split(",")
        if len(parties) != 2:
            return None
        e, n = int(parties[0]), int(parties[1])
        return (e, n)
    except:
        return None