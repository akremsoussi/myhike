# Archives VM à remettre

**Projet :** MyHike / Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

Les trois exports récents sont regroupés localement dans `ova/`, à la racine du projet. Ce dossier est exclu de l’historique Git. Les trois archives (environ 2,88 Go au total), le guide et leurs empreintes sont disponibles dans la [release GitHub du rendu](https://github.com/akremsoussi/myhike/releases/tag/rendu-2026-10-26).

- `vm-donnees.ova` : 910 198 784 octets.
- `vm-metier.ova` : 1 039 155 200 octets.
- `vm-proxy.ova` : 927 240 192 octets.

Les tailles correspondent à la passation d’Akrem. Les manifestes internes des trois archives ont été vérifiés après transfert ; les empreintes ci-dessous ont été calculées sur les fichiers reçus. Cela ne constitue pas un test d’import et de démarrage sur ce poste.

```text
a9139816274ce1f275254ca63bd5338a2e630317405cf6f9f1ecb0aa5533e571  vm-donnees.ova
9db9aea951b9196e556782284dd9a86fbe5420629f03a5e340a53640cff550f9  vm-metier.ova
fa8e02320ad18e67834b8d56f05602719f8febdf5f9517875c331112b1f04a5e  vm-proxy.ova
```

Dans VirtualBox, utiliser **Fichier → Importer un appareil virtuel** pour chaque archive. Vérifier le réseau interne `intnet-app` et la redirection du proxy vers le port hôte 8080. Ne pas démarrer simultanément les copies et les anciennes VM utilisant les mêmes IP, ni Docker sur le même port. Les exports ne contiennent pas l’historique des snapshots.

Les accès console sont à transmettre séparément si nécessaires. Ne pas joindre de clé SSH privée ou de fichier d’environnement au rendu.
