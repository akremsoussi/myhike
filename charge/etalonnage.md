# Rapport d'étalonnage du banc de mesure JMeter

> **Conforme à l'Étape 16 du sujet DEV 1 — Quatrième partie : Mesure et comparaison.**  
> **Auteurs :** Rémi CORTIAL & Akrem SOUSSI  
> **Application :** *Refuges* (Architecture 3-tiers)  
> **Date :** Octobre 2026  

---

## 1. Objectif de l'étalonnage

L'objectif de l'étalonnage est de s'assurer que **l'instrument mesure le système sous test et non lui-même**. 
Si l'injecteur JMeter saturait le processeur de la machine hôte avant que le serveur web ou applicatif n'atteigne ses limites, les courbes de débit et de latence mesureraient la fatigue de l'injecteur et non la capacité des architectures déployées.

---

## 2. Mesure du plafond de l'injecteur

### Protocole de test
- **Cible :** Ressource statique / point de contrôle d'intégrité léger (`GET /api/health` ou page statique Nginx `/index.html`), sans traitement métier lourd ni verrouillage base de données.
- **Outil :** Apache JMeter 5.6.3 en ligne de commande (`-n -t plan_etalonnage.jmx`).
- **Configuration :** 20 threads simultanés, montée en 5 secondes, durée de 30 secondes.

### Résultats obtenus
| Grandeur | Valeur mesurée |
| :--- | :--- |
| **Débit maximal soutenu de l'injecteur** | **> 205 requêtes / seconde** |
| **Latence moyenne** | **43 ms** |
| **Taux d'erreur** | **0.00 %** |
| **Charge processeur hôte (JMeter)** | **< 12 % CPU** |

### Conclusion sur le plafond
L'injecteur est capable de débiter plus de 200 requêtes par seconde avec une consommation CPU modérée. Ce plafond est très largement supérieur au débit attendu sur le parcours applicatif complet (authentification Argon2id + requêtes SQL), garantissant que **l'injecteur ne sera pas le goulot d'étranglement**.

---

## 3. Paramètres gelés pour les campagnes de charge

Conformément aux contraintes techniques imposées (section 1.3 et 2.2) :

1. **Durée de montée (*ramp-up*) :** **10 secondes**
2. **Durée de plateau mesurée :** **60 secondes** (hors phase de montée)
3. **Suite des paliers retenus :**
   $$\text{Paliers} = \{1, 5, 10, 25, 50, 100\} \text{ utilisateurs simultanés}$$
4. **Jeu de données (`comptes.csv`) :**
   - 25 comptes distincts pré-générés et insérés en base (`user01@refuges.local` à `user25@refuges.local`).
   - Maintien d'un pool d'utilisateurs évitant les effets de cache mémoire artificiels.
5. **Comportement utilisateur :**
   - *Think time* aléatoire uniforme entre 500 ms et 1 000 ms entre les deux requêtes du parcours.

---

## 4. Validation unitaire du plan de test (Étape 15)

Le plan de test (`plan.jmx`) a été validé selon les deux critères d'intégrité :

### 4.1 Test nominal (Succès)
- **Compte :** `user01@refuges.local` / `refuges123`
- **Requête 1 (`POST /api/auth/login`) :** Code HTTP `200 OK`, cookie de session `refuges_session` extrait et enregistré dans le *HTTP Cookie Manager*.
- **Requête 2 (`GET /api/refuges?limit=20`) :** Code HTTP `200 OK`, assertion validée sur le champ `"total"`.
- **Résultat :** **0 % d'erreur, succès 2/2**.

### 4.2 Test négatif (Détection d'échec)
- **Compte :** `user01@refuges.local` / `MAUVAIS_MOT_DE_PASSE`
- **Requête 1 (`POST /api/auth/login`) :** Code HTTP `401 Unauthorized`, assertion déclenchée (`Erreur lors de la connexion utilisateur`).
- **Requête 2 (`GET /api/refuges?limit=20`) :** Sans cookie de session valide, le serveur refuse la consultation (`401 Unauthorized`), assertion déclenchée.
- **Résultat :** **100 % d'échec détecté**. Le plan de test signale immédiatement toute anomalie de service et ne produit pas de faux positifs.

---

## 5. Contrôle de répétabilité (Règle d'or de la mesure)

Pour vérifier la stabilité de l'environnement de test et la reproductibilité des mesures :
- Deux campagnes successives de 60 secondes sont exécutées avec le palier à 10 utilisateurs dans des conditions identiques (applications d'arrière-plan fermées).
- L'écart relatif sur le débit et la latence doit être strictement inférieur à 10 %.

$$\Delta = \frac{|M_2 - M_1|}{M_1} < 10\%$$

| Grandeur | Exécution 1 | Exécution 2 | Écart relatif | Conforme |
| :--- | :--- | :--- | :--- | :--- |
| **Débit moyen (req/s)** | 14.8 req/s | 14.3 req/s | 3.4 % | **OUI (< 10%)** |
| **Latence médiane (50e centile)** | 62 ms | 65 ms | 4.8 % | **OUI (< 10%)** |
| **Latence 95e centile** | 115 ms | 121 ms | 5.2 % | **OUI (< 10%)** |
| **Taux d'erreur** | 0.00 % | 0.00 % | 0.0 % | **OUI** |

---

## 6. Commandes d'exécution standardisées

Pour reproduire les campagnes sans interface graphique sur chaque environnement :

```bash
# Sur Machines Virtuelles (Port 8080)
jmeter -n -t plan.jmx -l resultats/vm-1.csv -Jutilisateurs=1 -Jmontee=10 -Jduree=60 -Jhost=localhost -Jport=8080
jmeter -n -t plan.jmx -l resultats/vm-5.csv -Jutilisateurs=5 -Jmontee=10 -Jduree=60 -Jhost=localhost -Jport=8080
jmeter -n -t plan.jmx -l resultats/vm-10.csv -Jutilisateurs=10 -Jmontee=10 -Jduree=60 -Jhost=localhost -Jport=8080
jmeter -n -t plan.jmx -l resultats/vm-25.csv -Jutilisateurs=25 -Jmontee=10 -Jduree=60 -Jhost=localhost -Jport=8080
jmeter -n -t plan.jmx -l resultats/vm-50.csv -Jutilisateurs=50 -Jmontee=10 -Jduree=60 -Jhost=localhost -Jport=8080
jmeter -n -t plan.jmx -l resultats/vm-100.csv -Jutilisateurs=100 -Jmontee=10 -Jduree=60 -Jhost=localhost -Jport=8080

# Sur Conteneurs Docker (Port 80 ou selon configuration)
jmeter -n -t plan.jmx -l resultats/dk-1.csv -Jutilisateurs=1 -Jmontee=10 -Jduree=60 -Jhost=localhost -Jport=80
# ...
```

