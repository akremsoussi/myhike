# De la maquette Figma au site Refuges : notre démarche

**Projet :** MyHike / Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

[Voir notre maquette Figma](https://www.figma.com/design/KrPHETSktcZgtTbB9uxVyB/Refuges-%E2%80%93-Web-App?node-id=10-6)

*Nous n’avons pas conservé l’historique complet de nos échanges avec l’IA. Cette présentation reconstitue notre démarche ; les exemples de prompts sont reformulés pour expliquer nos intentions et ne sont pas les messages exacts envoyés à l’époque.*

## Organiser les fonctionnalités

Avec Refuges, nous voulions permettre aux utilisateurs de trouver un refuge, de consulter ses informations et de préparer des sorties avec d’autres randonneurs. Nous avons organisé l’interface autour de trois entrées principales : la carte, les communautés et les sorties. Les pages de connexion, de profil et de modération complètent ces parcours.

L’IA nous a servi d’appui pour structurer ces besoins et réfléchir à leur présentation. Nos demandes portaient d’abord sur l’organisation des écrans, avant de détailler leur apparence.

> « Nous travaillons sur une application de randonnée avec une carte des refuges, des communautés et des sorties. Propose une organisation des écrans et un parcours pour chercher un refuge, consulter sa fiche puis préparer une sortie. Prévois aussi la connexion et la modération. »

## Définir l’apparence de la maquette

Nous avons retenu une palette verte, des fonds clairs et des cartes blanches pour rappeler l’univers de la nature tout en gardant une interface lisible. Les boutons, les champs et les badges suivent les mêmes règles sur les différentes pages.

Notre interface reprend des principes courants des sites de cartographie et de randonnée : associer une carte à une liste de résultats, rendre la recherche visible et regrouper les informations pratiques dans une fiche. Nous n’avons pas conservé les références précises des sites consultés et ne pouvons donc pas attribuer ces inspirations à des sites particuliers.

> « Propose une interface sobre, dans un univers montagne et nature, avec une palette verte et une typographie lisible. Sur la page Carte, organise la recherche, les filtres et la liste des refuges sans surcharger l’écran. »

Nous avons ensuite affiné les demandes écran par écran : mettre les informations importantes en avant, alléger les éléments secondaires et conserver les mêmes composants. Cette approche permet de préciser ce que nous attendons de l’IA au lieu de lui demander simplement de produire une application entière.

> « Sur la fiche refuge, rends le nom, la localisation et les informations pratiques plus visibles. Reprends les boutons et les arrondis de la page Carte. Prévois un affichage sans photo et un message lorsqu’une recherche ne retourne aucun résultat. »

## Choisir les ressources et intégrer le site

Le site final utilise la police **Inter**, intégrée avec Fontsource, et les icônes **Lucide**. Les cartes interactives reposent sur **Leaflet et React Leaflet**, avec les tuiles **OpenStreetMap**. Les informations sur les refuges sont attribuées à **refuges.info** dans les cartes.

Ces ressources sont identifiables dans le code de l’application. Nous ne disposons pas d’un inventaire équivalent pour les images de la maquette et ne revendiquons donc aucune banque d’images ni génération d’images particulière.

Pour passer de la maquette au site, nous avons utilisé React et TypeScript. Les couleurs, les tailles et les arrondis sont centralisés dans des fichiers de styles communs, dont les commentaires font référence à la maquette Figma. Cela permet de conserver une présentation cohérente entre les pages.

L’intégration ajoute aussi les comportements nécessaires : navigation, connexion, chargement des données de l’API et interactions avec la carte.

> « Intègre cette page en React et TypeScript en reprenant les styles de la maquette et les composants existants. Relie-la aux données de l’API et prévois les états de chargement, d’erreur et de liste vide. Signale les adaptations nécessaires par rapport à la maquette. »

## Le rôle de l’IA dans notre travail

L’IA nous a accompagnés pour organiser les idées, proposer des solutions visuelles et aider à leur traduction en code. Notre rôle reste de préciser les besoins, de sélectionner les propositions adaptées au projet et de vérifier le résultat. La maquette donne une référence visuelle ; l’application doit ensuite rendre les parcours réellement utilisables.
