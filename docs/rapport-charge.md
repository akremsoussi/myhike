# Rapport d'analyse et de comparaison des performances (VMs vs Conteneurs)

> **Quatrième partie — Mesure et comparaison (Étape 18)**  
> **Auteurs :** Rémi CORTIAL & Akrem SOUSSI  
> **Cadre :** Polytech Marseille — Master 1 Informatique (DEV 1 : Application Trois-Tiers)  
> **Enseignant :** Mohamed Quafafou  
> **Statut du document :** Canevas méthodologique en attente des relevés bruts des campagnes (Étape 17)  

---

## 1. Contexte et Méthodologie

Ce rapport a pour objectif de comparer quantitativement et techniquement deux modes de déploiement de l'application trois-tiers *Refuges* :
1. **Trois Machines Virtuelles (VMs) :** Déploiement distribué isolé (VirtualBox, Ubuntu Server 24.04).
2. **Trois Conteneurs (Docker) :** Déploiement conteneurisé (Docker / Compose).

### Conditions expérimentales strictes (Règle d'or p. 52-53)
- **Même poste de travail :** Exécution séquentielle sur la même machine hôte, applications de fond fermées.
- **Un seul déploiement allumé à la fois :** Ne jamais faire tourner simultanément les VMs et les conteneurs (pour éviter tout partage CPU/mémoire parasite).
- **Même jeu de données :** Base MySQL réinitialisée avant chaque campagne via `donnees/peuplement.sql` (4 652 refuges, 25 comptes de test).
- **Même scénario JMeter :** `charge/plan.jmx` (connexion d'un utilisateur du pool, temporisation de 500 à 1 000 ms, consultation des refuges).
- **Paliers imposés :** 1, 5, 10, 25, 50, 100 utilisateurs simultanés avec 10 s de montée et 60 s de plateau de mesure.

---

## 2. Tableau de Synthèse Comparatif (Étape 18, page 56)

*Ce tableau compare les mesures réelles obtenues lors des campagnes de charge.*

| Grandeur | Trois machines virtuelles (Relevés réels) | Trois conteneurs (Docker) | Écart / Observations |
| :--- | :--- | :--- | :--- |
| **Débit maximal soutenu ($D_{\max}$)** | **5,17 req/s** (palier 10, stable ~4,8 req/s à 25 et 50) | *[À relever par Akrem - Étape 17]* | |
| **Charge au point de saturation** | **10 à 25 utilisateurs simultanés** | *[À relever par Akrem - Étape 17]* | |
| **Latence médiane ($L_{50}$) à charge 10** | **931 ms** | *[À relever par Akrem - Étape 17]* | |
| **Latence au 95e centile ($L_{95}$) à charge 10** | **2 585 ms** | *[À relever par Akrem - Étape 17]* | |
| **Taux d'erreur à charge nominale ($\le 50$)**| **0,00 %** (0/521 à 10 u., 0/723 à 25 u., 0/309 à 50 u.) | *[À relever par Akrem - Étape 17]* | |
| **Taux d'erreur en écroulement (charge 100)**| **34,12 %** (58 erreurs 500 sur 170 requêtes) | *[À relever par Akrem - Étape 17]* | |
| **Goulots d'étranglement identifiés** | **1. CPU Argon2id (10-50 u.)**<br>**2. Pool de connexions DB / Timeout (100 u.)** | *[À nommer]* | |
| **Temps de démarrage complet** | ~45 s | *[Relevé Étape 14]* | |
| **Mémoire consommée au repos** | ~2 400 Mo (3 instances Ubuntu) | *[Relevé Étape 14]* | |

---

### Tableau détaillé de la série Machines Virtuelles (Relevés bruts `vm-*.csv`)

| Palier | Utilisateurs virtuels | Échantillons | Débit réel (req/s) | Latence médiane ($L_{50}$) | Latence 95e centile ($L_{95}$) | Taux d'erreur | CPU `vm-metier` | Comportement système |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | 1 | 106 | **1,09 req/s** | 188 ms | 342 ms | 0,00 % | 2,5 % (max 3,5%) | Régime nominal sans concurrence |
| **2** | 5 | 425 | **4,21 req/s** | 310 ms | 1 138 ms | 0,00 % | 8,0 % (max 11,5%) | Montée linéaire du débit ($\times 3,9$) |
| **3** | 10 | 521 | **5,17 req/s** | 931 ms | 2 585 ms | 0,00 % | 10,4 % (max 16,7%) | Début d'inflexion du débit, latence s'allonge |
| **4** | 25 | 723 | **4,87 req/s** | 3 917 ms | 6 770 ms | 0,00 % | 13,2 % (max 19,8%) | **Saturation :** débit plafonné, latence $\times 4$ |
| **5** | 50 | 309 | **4,82 req/s** | 8 280 ms | 12 826 ms | 0,00 % | 11,2 % (max 19,1%) | **Surcharge :** débit bloqué à 4,8 req/s, zéro erreur |
| **6** | 100 | 170 | **1,83 req/s** | 35 894 ms | 60 005 ms | **34,12 %** | Pics à 26,6% puis chutes | **Écroulement :** saturation pool DB, timeouts 60s, débit $\div 2,6$ |

---

## 3. Courbes de Performances (à tracer après campagnes)

1. **Débit (requêtes/seconde) en fonction du nombre d'utilisateurs :**
   - Identifier le point où la courbe cesse de croître (saturation).
2. **Latence au 95e centile et médiane :**
   - Observer l'inflexion exponentielle liée à l'allongement de la file d'attente réseau/OS.
3. **Taux d'erreur (%) :**
   - Consigner l'apparition des premiers codes d'erreur (ex: 502 Bad Gateway ou 504 Gateway Timeout).

---

## 4. Analyse Technique (Les 4 Questions Imposées p. 57)

*Les réponses seront rédigées une fois les données brutes consolidées :*

### 4.1 De combien les deux déploiements diffèrent-ils, chiffres à l'appui ?
*[À rédiger : Comparaison chiffrée exacte du débit maximal, du temps de boot, de la consommation RAM et de la latence au 95e centile.]*

### 4.2 Quelle propriété technique explique cet écart ?
*[À rédiger : Analyse architecturale comparant l'émulation matérielle / hyperviseur / noyaux invités multiples de VirtualBox face à l'isolation légère par namespaces / cgroups partageant le noyau hôte sous Docker.]*

### 4.3 Quel composant cède en premier, dans chaque cas ?
*[À rédiger : Corrélation avec les métriques serveur relevées pendant les paliers (CPU Uvicorn/Argon2id, I/O disque MySQL, mémoire, sockets Nginx) pour nommer le composant limitant.]*

### 4.4 Que ne dit pas cette mesure ? (Limites de l'étude)
*[À rédiger : Biais de l'exécution sur une même machine hôte physique, volume de données tenant en cache mémoire RAM, absence de test de tolérance aux pannes ou de scalabilité multi-nœuds physique.]*
