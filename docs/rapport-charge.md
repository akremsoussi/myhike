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

*Ce tableau sera rempli à partir des métriques extraites des fichiers bruts `charge/resultats/vm-*.csv` et `charge/resultats/dk-*.csv` et des relevés système (`htop` / `vmstat`).*

| Grandeur | Trois machines virtuelles | Trois conteneurs | Écart / Observations |
| :--- | :--- | :--- | :--- |
| **Débit maximal soutenu** | *[À relever - Étape 17]* | *[À relever - Étape 17]* | |
| **Charge au point de saturation** | *[À relever - Étape 17]* | *[À relever - Étape 17]* | |
| **Latence au 95e centile, à charge égale** | *[À relever - Étape 17]* | *[À relever - Étape 17]* | |
| **Goulot d'étranglement identifié** | *[À nommer]* | *[À nommer]* | |
| **Temps de démarrage complet** | *[Relevé Étape 10]* | *[Relevé Étape 14]* | |
| **Mémoire consommée au repos** | *[Relevé Étape 10]* | *[Relevé Étape 14]* | |

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
