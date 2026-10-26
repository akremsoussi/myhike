# MyHike / Refuges — Diagrammes du projet

Diagrammes établis le 26 octobre 2026 à partir du code et du schéma SQL locaux.
Ouvrir **index.html** pour le visualiseur hors ligne, ou directement un fichier SVG/PNG.

## Contenu

1. **Base de données** : 19 tables applicatives, clés et cardinalités.
2. **Cas d’utilisation** : visiteur, utilisateur actif, modérateur et super-administrateur.
3. **Classes métier** : les 18 classes persistantes SQLAlchemy réellement présentes.
4. **Séquence** : connexion puis requête protégée de consultation des refuges.
5. **Architecture trois tiers** : présentation, métier, données et intégrations.
6. **Schéma SQL complet** : 20 tables, 135 colonnes et 34 clés étrangères, avec Alembic.

Les SVG restent nets à toute échelle. Les PNG peuvent être insérés dans Word ou
PowerPoint. Les fichiers `.mmd` sont les sources Mermaid ; `.puml` est la source
PlantUML du diagramme de cas d’utilisation. `DIAGRAMS.md` réunit les sources.

## Conventions et périmètre

- Les explications sont en français. Les noms des tables, colonnes, classes,
  fonctions, routes, valeurs d’énumération et types restent ceux du code.
- ER : `PK` = clé primaire, `FK` = clé étrangère, `UK` = unicité sur une colonne.
  « Facultatif » indique une colonne nullable. Les cardinalités sont déduites
  des contraintes SQL ; un parent n’est pas obligé de posséder des enfants.
  Les unicités composites, types SQL détaillés et actions de suppression sont
  conservés dans `database-schema.json` et dans le schéma SQL du projet.
- Les liens ER pleins sont identifiants (clé étrangère incluse dans la clé
  primaire). Les liens pointillés sont non identifiants : ils ne désignent
  pas systématiquement une suppression en cascade.
- Les associations du diagramme de classes correspondent aux clés étrangères,
  y compris celles sans `relationship()` explicite. `Community.refuges` est une
  relation plusieurs-à-plusieurs via `community_refuges`, et non une classe inventée.
- Les classes persistantes héritent de `Base` SQLAlchemy. Les flèches d’héritage
  répétitives, les classes du framework, les schémas DTO et la plupart des
  déclarations d’énumérations sont omis pour la lisibilité. Les attributs sont
  sélectionnés ; les propriétés calculées existent réellement dans le code.
  Les opérations métier résident dans les modules de services et les routes.
- Les rôles sont des valeurs de `User.role`, pas des sous-classes persistantes.
  Un modérateur hérite des droits utilisateur, et un super-administrateur des
  droits de modération. Les pages de connexion et d’inscription sont réservées
  aux visiteurs non connectés. Un compte non confirmé peut se connecter mais
  ne peut pas accéder aux fonctions réservées aux comptes actifs.
- Les cas d’utilisation regroupent certains objectifs pour rester lisibles.
  Les règles de confidentialité, propriété, invitation et capacité s’appliquent.
  Un modérateur ordinaire ne peut pas sanctionner un administrateur. Les
  super-administrateurs sont protégés et les auto-sanctions interdites.
  Seuls les super-administrateurs peuvent modifier les rôles.
- La séquence représente deux requêtes distinctes : connexion puis lecture
  protégée. Les erreurs sont des branches alternatives. Les requêtes internes
  de rafraîchissement ORM sont simplifiées. Une Session SQLAlchemy par requête
  ne correspond pas nécessairement à une seule requête SQL.
- Les photos de refuges.info sont importées par des scripts, converties en WebP,
  stockées localement puis servies par `/api/media/...`. Ouvrir une fiche ne
  déclenche pas un import en direct depuis le service externe.
- Docker publie uniquement `localhost:8080`. Les ports API `8000` et MySQL `3306`
  sont internes. En développement local, Vite `5173` remplace Nginx et relaie `/api`.

## Vérification et traçabilité

Les colonnes des modèles ORM correspondent au schéma SQL analysé.
`source-manifest.json` contient les chemins sources et leurs empreintes SHA-256.
Les diagrammes ont été rendus puis inspectés ; les onglets et le zoom du visualiseur
ont été vérifiés. Le schéma a été analysé sans modifier la base active.
Aucun mot de passe, contenu de base, fichier de sauvegarde ou photo n’est inclus.
