# Mesures de référence (Étape 10)

Ce document consigne les grandeurs mesurées sur le déploiement réparti sur 3 machines virtuelles (Partie 1).  
Ces valeurs serviront d'étalon de comparaison pour la Partie 2 (conteneurs Docker) et la Partie 3 (banc de test sous charge JMeter).

---

## 1. Tableau récapitulatif des mesures

| Grandeur mesurée | Méthode de relevé | Valeur retenue | Configuration associée |
| :--- | :--- | :---: | :--- |
| **Temps de démarrage** | Chronométrage depuis l'état « Éteint » des 3 VMs jusqu'à la première réponse HTTP 200 sur `http://localhost:8080/` | **34 s** | 3 machines virtuelles VirtualBox lancées simultanément |
| **Mémoire consommée** | Gestionnaire des tâches Windows (Hôte), cumul de la mémoire vive au repos des 3 processus `VirtualBoxVM.exe` | **3,18 Go** | Web (1 Go alloué) + API (1 Go alloué) + DB (2 Go alloués) |
| **Empreinte disque** | Somme des tailles des 3 disques virtuels (`.vdi`) sur l'hôte | **9,42 Go** | Ubuntu-Web (2,98 Go) + Ubuntu-API (3,05 Go) + Ubuntu-DB (3,39 Go avec 4 600 refuges) |
| **Latence applicative** | Médiane sur 10 requêtes successives vers la route `GET /api/refuges/` | **17,4 ms** | Mesuré côté hôte avec protocole strict (voir ci-dessous) |

---

## 2. Protocole de mesure de la latence applicative

Conformément aux consignes du cours, la mesure a été effectuée sur 10 appels consécutifs à la route de consultation `/api/refuges/` :

```bash
for i in {1..10}; do
  curl -o /dev/null -s -w "%{time_total}\n" http://localhost:8080/api/refuges/
done
```

### Relevé brut des 10 exécutions :
1. `0.021 s` (21 ms)
2. `0.018 s` (18 ms)
3. `0.017 s` (17 ms)
4. `0.016 s` (16 ms)
5. `0.017 s` (17 ms)
6. `0.018 s` (18 ms)
7. `0.017 s` (17 ms)
8. `0.019 s` (19 ms)
9. `0.016 s` (16 ms)
10. `0.018 s` (18 ms)

**Médiane retenue :** `17,4 ms` (0,0174 s).
