# SAE_3.02 - Routage en Oignon

**Auteur :** AANZOUR Mohamed-amine

---

## Description du projet

Ce projet consiste à concevoir un **système de communication anonyme** basé sur un ensemble de routeurs virtuels. Chaque message envoyé par un client traverse plusieurs routeurs sélectionnés aléatoirement avant d'atteindre sa destination .

Le projet se compose de :
- **Un Master** : centralise les données, propose une interface graphique de supervision
- **Plusieurs routeurs** : reçoivent, déchiffrent une couche RSA et relaient les messages
- **Des clients** : permettent l'envoi et la réception de messages anonymes
- **Une base de données MariaDB** : stocke les routeurs, clients, leurs adresses IP, ports et clés publiques

---

## Fonctionnalités principales

### Master
- Enregistrement automatique des routeurs et clients
- Interface graphique PyQt6 (visualisation temps réel, statistiques, logs)
- Surveillance automatique de l'état des nœuds
- Communication avec la base de données MariaDB

### Routeurs
- Génération automatique de clés RSA au démarrage
- Déchiffrement d'une seule couche du message (routage en oignon)
- **Anonymisation complète** : ne connaît que le prochain saut
- Logging anonyme

### Clients
- Interface graphique PyQt6 
- Envoi de messages chiffrés en couches multiples (RSA)
- Réception avec identification de l'expéditeur
- Sélection du nombre de sauts et des routeurs

---

## Schéma de fonctionnement

```
Client A → chiffre en 3 couches RSA
    ↓
[Routeur1] → déchiffre couche 1 → voit uniquement : Routeur2
    ↓
[Routeur2] → déchiffre couche 2 → voit uniquement : Routeur3
    ↓
[Routeur3] → déchiffre couche 3 → voit uniquement : Client B
    ↓
Client B → reçoit le message
```

**Aucun routeur ne connaît l'origine réelle, la destination finale ou le contenu du message.**

---

## Technologies utilisées

- **Python 3.+**
- **PyQt6** (interface graphique)
- **MariaDB 10.x** (base de données)
- **Sockets TCP** (communication réseau)
- **RSA** (chiffrement multicouche)


## Documentation

Pour toute aide d'installation ou de configuration, veuillez vous référer aux **documents d'installation** se trouvant dans le dossier `Documentation/`.

Vous y retrouverez aussi une **vidéo de démonstration** du fonctionnement du projet avec différentes explications.

Les codes source se situent dans le dossier `Source/` 



