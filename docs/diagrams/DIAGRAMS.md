# Refuges — Code Mermaid de tous les diagrammes

**Projet :** Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

Chaque bloc est autonome : copier un seul bloc à la fois dans un éditeur Mermaid.
Les libellés sont en français ; les identifiants techniques correspondent au projet.

**Cas d’utilisation :** Mermaid ne possède pas de notation UML native pour ce type de diagramme.
La version ci-dessous utilise `flowchart` pour représenter les acteurs, les objectifs et l’héritage des droits.
La version UML formelle reste disponible dans `02-use-cases.puml`.

## Relations de la base de données

Diagramme entité-association : tables applicatives, clés, liens facultatifs et cardinalités.

```mermaid
erDiagram
    communities {
        bigint id PK "obligatoire"
        varchar name "obligatoire"
        bigint massif_id FK "facultatif"
        bigint banner_id FK "facultatif"
        bigint icon_id FK "facultatif"
    }
    community_members {
        bigint community_id PK, FK "obligatoire"
        bigint user_id PK, FK "obligatoire"
    }
    community_refuges {
        bigint community_id PK, FK "obligatoire"
        bigint refuge_id PK, FK "obligatoire"
    }
    email_tokens {
        bigint id PK "obligatoire"
        bigint user_id FK "obligatoire"
        varchar email "obligatoire"
    }
    friendships {
        bigint id PK "obligatoire"
        bigint requester_id FK "obligatoire"
        bigint addressee_id FK "obligatoire"
        enum status "obligatoire"
    }
    massifs {
        bigint id PK "obligatoire"
        varchar name "obligatoire"
    }
    moderation_log {
        bigint id PK "obligatoire"
        bigint actor_id FK "facultatif"
    }
    outing_invitations {
        bigint outing_id PK, FK "obligatoire"
        bigint user_id PK, FK "obligatoire"
        bigint invited_by_id FK "obligatoire"
    }
    outing_participants {
        bigint outing_id PK, FK "obligatoire"
        bigint user_id PK, FK "obligatoire"
    }
    outing_stops {
        bigint id PK "obligatoire"
        bigint outing_id FK "obligatoire"
        bigint refuge_id FK "facultatif"
        varchar name "obligatoire"
    }
    outings {
        bigint id PK "obligatoire"
        varchar title "obligatoire"
        bigint organizer_id FK "obligatoire"
        enum visibility "obligatoire"
    }
    post_likes {
        bigint post_id PK, FK "obligatoire"
        bigint user_id PK, FK "obligatoire"
    }
    posts {
        bigint id PK "obligatoire"
        bigint author_id FK "obligatoire"
        bigint community_id FK "facultatif"
        enum visibility "obligatoire"
        bigint refuge_id FK "facultatif"
    }
    refuge_photos {
        bigint id PK "obligatoire"
        bigint refuge_id FK "obligatoire"
        bigint upload_id FK, UK "obligatoire"
    }
    refuges {
        bigint id PK "obligatoire"
        varchar name "obligatoire"
        bigint massif_id FK "facultatif"
    }
    reports {
        bigint id PK "obligatoire"
        bigint reporter_id FK "obligatoire"
        bigint target_id FK "obligatoire"
        bigint post_id FK "facultatif"
        enum reason "obligatoire"
        bigint resolved_by_id FK "facultatif"
    }
    sessions {
        bigint id PK "obligatoire"
        bigint user_id FK "obligatoire"
    }
    uploads {
        bigint id PK "obligatoire"
        varchar key UK "obligatoire"
        bigint owner_id FK "facultatif"
        bigint post_id FK "facultatif"
    }
    users {
        bigint id PK "obligatoire"
        varchar username UK "obligatoire"
        varchar email UK "obligatoire"
        enum role "obligatoire"
        enum status "obligatoire"
    }
    uploads |o..o{ communities : "banner_id"
    uploads |o..o{ communities : "icon_id"
    massifs |o..o{ communities : "massif_id"
    communities ||--o{ community_members : "community_id"
    users ||--o{ community_members : "user_id"
    communities ||--o{ community_refuges : "community_id"
    refuges ||--o{ community_refuges : "refuge_id"
    users ||..o{ email_tokens : "user_id"
    users ||..o{ friendships : "addressee_id"
    users ||..o{ friendships : "requester_id"
    users |o..o{ moderation_log : "actor_id"
    users ||..o{ outing_invitations : "invited_by_id"
    outings ||--o{ outing_invitations : "outing_id"
    users ||--o{ outing_invitations : "user_id"
    outings ||--o{ outing_participants : "outing_id"
    users ||--o{ outing_participants : "user_id"
    outings ||..o{ outing_stops : "outing_id"
    refuges |o..o{ outing_stops : "refuge_id"
    users ||..o{ outings : "organizer_id"
    posts ||--o{ post_likes : "post_id"
    users ||--o{ post_likes : "user_id"
    users ||..o{ posts : "author_id"
    communities |o..o{ posts : "community_id"
    refuges |o..o{ posts : "refuge_id"
    refuges ||..o{ refuge_photos : "refuge_id"
    uploads ||..o| refuge_photos : "upload_id"
    massifs |o..o{ refuges : "massif_id"
    posts |o..o{ reports : "post_id"
    users ||..o{ reports : "reporter_id"
    users |o..o{ reports : "resolved_by_id"
    users ||..o{ reports : "target_id"
    users ||..o{ sessions : "user_id"
    users |o..o{ uploads : "owner_id"
    posts |o..o{ uploads : "post_id"
```

## Cas d’utilisation

Acteurs, fonctionnalités et héritage des droits selon les règles réellement implémentées.

```mermaid
flowchart LR
    %% Représentation des cas d’utilisation avec la syntaxe flowchart.
    %% Les flèches pointillées expriment l’héritage des droits, pas une séquence.
    V["Acteur : Visiteur"]
    U["Acteur : Utilisateur actif"]
    M["Acteur : Modérateur"]
    S["Acteur : Super-administrateur"]
    M -. "hérite des droits" .-> U
    S -. "hérite des droits" .-> M
    subgraph APP["Refuges"]
        direction TB
        UC0(["Créer un compte"])
        UC1(["Se connecter"])
        UC2(["Confirmer l’adresse e-mail"])
        UC3(["Réinitialiser un mot de passe oublié"])
        UC4(["Explorer la carte et les fiches des refuges"])
        UC5(["Rechercher des refuges, communautés et utilisateurs"])
        UC6(["Rejoindre ou quitter une communauté"])
        UC7(["Publier avec des photos ou une trace GPX"])
        UC8(["Aimer des publications et gérer ses propres publications"])
        UC9(["Gérer son profil, sa confidentialité et ses amis"])
        UC10(["Organiser des sorties et inviter des participants"])
        UC11(["Rejoindre ou quitter une sortie"])
        UC12(["Signaler un compte ou une publication"])
        UC13(["Se déconnecter"])
        UC14(["Examiner et traiter les signalements"])
        UC15(["Supprimer des publications inappropriées"])
        UC16(["Créer, modifier ou supprimer des communautés"])
        UC17(["Gérer les comptes utilisateurs classiques"])
        UC18(["Promouvoir ou rétrograder des modérateurs"])
        UC19(["Gérer les comptes des modérateurs"])
    end
    V --- UC0
    V --- UC1
    V --- UC2
    V --- UC3
    U --- UC4
    U --- UC5
    U --- UC6
    U --- UC7
    U --- UC8
    U --- UC9
    U --- UC10
    U --- UC11
    U --- UC12
    U --- UC13
    M --- UC14
    M --- UC15
    M --- UC16
    M --- UC17
    S --- UC18
    S --- UC19
    N1["Compte actif et adresse confirmée requis pour les fonctions utilisateur."]
    N2["Les super-administrateurs sont protégés ; les auto-sanctions sont interdites."]
    N3["Les conditions et le statut du service sont accessibles à tous."]
    U -.-> N1
    S -.-> N2
    V -.-> N3
    classDef acteur fill:#edf7f2,stroke:#28765a,color:#153f31,stroke-width:2px;
    classDef note fill:#fff8e7,stroke:#cfad58,color:#5a4920;
    class V,U,M,S acteur;
    class N1,N2,N3 note;
```

## Classes métier

Classes SQLAlchemy réelles, principaux attributs, associations et propriétés calculées.

```mermaid
classDiagram
direction LR
    class Upload {
        +int id
        +str key
        +int owner_id
        +int width
        +int height
        +int post_id
        +url : propriété calculée
    }
    class Report {
        +int id
        +int reporter_id
        +int target_id
        +int post_id
        +ReportReason reason
        +int resolved_by_id
    }
    class ModerationLog {
        +int id
        +int actor_id
        +str message
        +datetime created_at
    }
    class Outing {
        +int id
        +str title
        +int organizer_id
        +datetime starts_at
        +int max_participants
        +OutingVisibility visibility
        +JSON path
    }
    class OutingStop {
        +int id
        +int outing_id
        +int position
        +int refuge_id
        +str name
    }
    class OutingParticipant {
        +int outing_id
        +int user_id
        +datetime joined_at
    }
    class OutingInvitation {
        +int outing_id
        +int user_id
        +int invited_by_id
        +datetime created_at
    }
    class Massif {
        +int id
        +int external_id
        +str name
    }
    class Refuge {
        +int id
        +int external_id
        +str name
        +RefugeKind kind
        +Decimal latitude
        +Decimal longitude
        +int altitude
        +int capacity
        +int massif_id
        +is_guarded : propriété calculée
        +phone : propriété calculée
    }
    class RefugePhoto {
        +int id
        +int refuge_id
        +int upload_id
        +int external_id
        +str author
        +url : propriété calculée
        +width : propriété calculée
        +height : propriété calculée
    }
    class Community {
        +int id
        +str slug
        +str name
        +str region
        +int massif_id
        +int banner_id
        +int icon_id
    }
    class CommunityMember {
        +int community_id
        +int user_id
        +datetime joined_at
    }
    class Friendship {
        +int id
        +int requester_id
        +int addressee_id
        +FriendshipStatus status
        +datetime created_at
    }
    class Post {
        +int id
        +int author_id
        +int community_id
        +str body
        +Visibility visibility
        +int refuge_id
        +JSON path
        +int distance_m
        +int elevation_gain_m
    }
    class PostLike {
        +int post_id
        +int user_id
        +datetime created_at
    }
    class User {
        +int id
        +str username
        +str email
        +str bio
        +Role role
        +AccountStatus status
    }
    class EmailToken {
        +int id
        +int user_id
        +TokenPurpose purpose
        +str token_hash
        +str email
    }
    class UserSession {
        +int id
        +int user_id
        +str token_hash
        +datetime created_at
        +datetime expires_at
    }
    Upload "0..1" -- "0..*" Community : banner_id
    Upload "0..1" -- "0..*" Community : icon_id
    Massif "0..1" -- "0..*" Community : massif_id
    Community "1" -- "0..*" CommunityMember : community_id
    User "1" -- "0..*" CommunityMember : user_id
    User "1" -- "0..*" EmailToken : user_id
    User "1" -- "0..*" Friendship : addressee_id
    User "1" -- "0..*" Friendship : requester_id
    User "0..1" -- "0..*" ModerationLog : actor_id
    User "1" -- "0..*" OutingInvitation : invited_by_id
    Outing "1" -- "0..*" OutingInvitation : outing_id
    User "1" -- "0..*" OutingInvitation : user_id
    Outing "1" -- "0..*" OutingParticipant : outing_id
    User "1" -- "0..*" OutingParticipant : user_id
    Outing "1" -- "0..*" OutingStop : outing_id
    Refuge "0..1" -- "0..*" OutingStop : refuge_id
    User "1" -- "0..*" Outing : organizer_id
    Post "1" -- "0..*" PostLike : post_id
    User "1" -- "0..*" PostLike : user_id
    User "1" -- "0..*" Post : author_id
    Community "0..1" -- "0..*" Post : community_id
    Refuge "0..1" -- "0..*" Post : refuge_id
    Refuge "1" -- "0..*" RefugePhoto : refuge_id
    Upload "1" -- "0..1" RefugePhoto : upload_id
    Massif "0..1" -- "0..*" Refuge : massif_id
    Post "0..1" -- "0..*" Report : post_id
    User "1" -- "0..*" Report : reporter_id
    User "0..1" -- "0..*" Report : resolved_by_id
    User "1" -- "0..*" Report : target_id
    User "1" -- "0..*" UserSession : user_id
    User "0..1" -- "0..*" Upload : owner_id
    Post "0..1" -- "0..*" Upload : post_id
    Community "0..*" -- "0..*" Refuge : refuges via community_refuges
```

## Séquence des requêtes

Connexion, création du cookie de session, contrôle des droits et consultation des refuges.

```mermaid
sequenceDiagram
    autonumber
    actor U as Utilisateur
    participant B as Navigateur / React
    participant N as Proxy Nginx
    participant A as Routes FastAPI et dépendances
    participant S as Modules accounts et security
    participant D as MySQL / SQLAlchemy
    U->>B: Saisir l’e-mail et le mot de passe
    B->>N: POST /api/auth/login (JSON)
    N->>A: Transmettre au serveur métier :8000
    A->>S: authenticate(db, email, password)
    S->>D: SELECT utilisateur par e-mail
    D-->>S: Utilisateur et empreinte Argon2id, ou absence de résultat
    S->>S: Vérifier le mot de passe avec Argon2id
    alt Identifiants incorrects
        S-->>A: ApiError 401 invalid_credentials
        A-->>N: 401 erreur JSON
        N-->>B: Afficher l’erreur de connexion
    else Compte suspendu
        S-->>A: ApiError 403 account_suspended
        A-->>N: 403 erreur JSON
        N-->>B: Afficher le refus d’accès
    else Identifiants valides et compte non suspendu
        S-->>A: Utilisateur
        A->>S: create_session(db, user)
        S->>S: Générer un jeton aléatoire et son empreinte SHA-256
        S->>D: INSERT sessions(token_hash, user_id, expires_at) et COMMIT
        D-->>S: Session enregistrée
        S-->>A: Jeton brut destiné au cookie
        A-->>N: 200 MeOut + Set-Cookie: refuges_session
        N-->>B: Enregistrer le cookie HttpOnly / SameSite=Lax
    end
    Note over B,D: La requête protégée suppose une connexion réussie. Un compte non confirmé ne peut pas accéder à la carte.
    U->>B: Ouvrir la carte des refuges
    B->>N: GET /api/refuges?limit=20 + cookie de session
    N->>A: Transmettre la requête
    A->>S: session_user(db, jeton du cookie)
    S->>S: Calculer le SHA-256 du jeton reçu dans le cookie
    S->>D: SELECT session non révoquée, non expirée et utilisateur associé
    D-->>S: Session et utilisateur, ou absence de résultat
    S-->>A: Utilisateur ou None
    A->>A: get_current_user + require_active
    alt Session absente, expirée ou révoquée
        A-->>N: 401 not_authenticated
        N-->>B: Erreur JSON / connexion nécessaire
    else Compte suspendu ou adresse e-mail non confirmée
        A-->>N: 403 account_suspended / account_pending
        N-->>B: Accès refusé / confirmation nécessaire
    else Utilisateur actif
        A->>D: COUNT des refuges correspondant aux filtres
        D-->>A: Nombre total
        A->>D: SELECT refuges LEFT JOIN massifs ORDER BY name, id LIMIT 20
        D-->>A: Objets ORM
        A->>A: Construire les schémas RefugeList / RefugeSummary
        A-->>N: 200 JSON (total, items)
        N-->>B: Réponse JSON
        B-->>U: Afficher la carte et la liste des refuges
    end
    Note over A,D: Une Session SQLAlchemy est créée par requête puis fermée. Les requêtes internes de rafraîchissement ORM sont simplifiées.
```

## Architecture trois tiers

Interface, proxy inverse, serveur métier, stockage SQL et services externes.

```mermaid
flowchart TB
    U["Utilisateur / navigateur"]
    subgraph PRESENTATION["Couche présentation"]
        R["React 19 + TypeScript + Leaflet<br/>Interface, navigation, carte et formulaires"]
        N["Nginx :80 dans le conteneur<br/>hôte localhost:8080<br/>Fichiers SPA et proxy inverse /api"]
    end
    subgraph BUSINESS["Couche métier"]
        A["FastAPI / Uvicorn :8000<br/>Routes, schémas de validation et dépendances"]
        S["Modules de services<br/>accounts, visibility, outings, posts, media…"]
        O["Modèles SQLAlchemy et Session par requête<br/>PyMySQL / utf8mb4"]
        I["Scripts d’import en ligne de commande<br/>import_refuges / import_refuge_photos"]
    end
    subgraph DATA["Données et stockage des fichiers"]
        D[("MySQL 8.4 :3306<br/>users, sessions, refuges, posts…")]
        F[("Volume uploads<br/>Images au format WebP")]
    end
    E["API refuges.info<br/>Source externe de données et de photos"]
    M["Envoi des e-mails<br/>Console par défaut / SMTP si configuré"]
    U --> R
    R -->|"HTTP /api et cookie de session"| N
    N -->|"Transmettre les requêtes /api"| A
    A --> S
    A --> O
    S --> O
    O -->|"SQL"| D
    S -->|"Lire et écrire les fichiers image"| F
    S --> M
    I -->|"Importer les données via l’ORM"| O
    I -->|"Récupérer les données et copier les photos"| E
    I -->|"Stocker les images converties en WebP"| F
    N -.->|"Servir l’interface compilée"| R
    NOTE["Le navigateur ne charge pas les photos directement depuis refuges.info.<br/>Il utilise /api/media/key.webp sur le serveur métier.<br/>En développement, Vite :5173 et son proxy /api remplacent Nginx."]
    A -.-> NOTE
```

## Schéma SQL complet

Toutes les tables et colonnes de schema.sql, y compris le suivi de version Alembic.

```mermaid
erDiagram
    alembic_version {
        varchar version_num PK "obligatoire"
    }
    communities {
        bigint id PK "obligatoire"
        varchar slug UK "obligatoire"
        varchar name "obligatoire"
        text description "obligatoire"
        varchar region "obligatoire"
        bigint massif_id FK "facultatif"
        datetime created_at "obligatoire"
        bigint banner_id FK "facultatif"
        bigint icon_id FK "facultatif"
    }
    community_members {
        bigint community_id PK, FK "obligatoire"
        bigint user_id PK, FK "obligatoire"
        datetime joined_at "obligatoire"
    }
    community_refuges {
        bigint community_id PK, FK "obligatoire"
        bigint refuge_id PK, FK "obligatoire"
    }
    email_tokens {
        bigint id PK "obligatoire"
        bigint user_id FK "obligatoire"
        enum purpose "obligatoire"
        varchar token_hash UK "obligatoire"
        varchar email "obligatoire"
        datetime created_at "obligatoire"
        datetime expires_at "obligatoire"
        datetime used_at "facultatif"
    }
    friendships {
        bigint id PK "obligatoire"
        bigint requester_id FK "obligatoire"
        bigint addressee_id FK "obligatoire"
        enum status "obligatoire"
        datetime created_at "obligatoire"
        datetime responded_at "facultatif"
    }
    massifs {
        bigint id PK "obligatoire"
        int external_id UK "obligatoire"
        varchar name "obligatoire"
    }
    moderation_log {
        bigint id PK "obligatoire"
        bigint actor_id FK "facultatif"
        varchar message "obligatoire"
        datetime created_at "obligatoire"
    }
    outing_invitations {
        bigint outing_id PK, FK "obligatoire"
        bigint user_id PK, FK "obligatoire"
        bigint invited_by_id FK "obligatoire"
        datetime created_at "obligatoire"
    }
    outing_participants {
        bigint outing_id PK, FK "obligatoire"
        bigint user_id PK, FK "obligatoire"
        datetime joined_at "obligatoire"
    }
    outing_stops {
        bigint id PK "obligatoire"
        bigint outing_id FK "obligatoire"
        int position "obligatoire"
        bigint refuge_id FK "facultatif"
        varchar name "obligatoire"
        decimal latitude "obligatoire"
        decimal longitude "obligatoire"
    }
    outings {
        bigint id PK "obligatoire"
        varchar title "obligatoire"
        bigint organizer_id FK "obligatoire"
        datetime starts_at "obligatoire"
        int max_participants "obligatoire"
        enum visibility "obligatoire"
        json path "obligatoire"
        datetime created_at "obligatoire"
    }
    post_likes {
        bigint post_id PK, FK "obligatoire"
        bigint user_id PK, FK "obligatoire"
        datetime created_at "obligatoire"
    }
    posts {
        bigint id PK "obligatoire"
        bigint author_id FK "obligatoire"
        bigint community_id FK "facultatif"
        text body "obligatoire"
        enum visibility "obligatoire"
        datetime created_at "obligatoire"
        bigint refuge_id FK "facultatif"
        json path "facultatif"
        int distance_m "facultatif"
        int elevation_gain_m "facultatif"
    }
    refuge_photos {
        bigint id PK "obligatoire"
        bigint refuge_id FK "obligatoire"
        bigint upload_id FK, UK "obligatoire"
        int external_id UK "obligatoire"
        varchar author "obligatoire"
        varchar caption "obligatoire"
        datetime taken_at "facultatif"
        int position "obligatoire"
    }
    refuges {
        bigint id PK "obligatoire"
        int external_id UK "obligatoire"
        varchar name "obligatoire"
        enum kind "obligatoire"
        decimal latitude "obligatoire"
        decimal longitude "obligatoire"
        int altitude "facultatif"
        int capacity "facultatif"
        bigint massif_id FK "facultatif"
        varchar state "facultatif"
        text access "facultatif"
        text remarks "facultatif"
        text owner_info "facultatif"
        varchar source_url "facultatif"
        datetime source_updated_at "facultatif"
        datetime imported_at "obligatoire"
        datetime photos_checked_at "facultatif"
    }
    reports {
        bigint id PK "obligatoire"
        bigint reporter_id FK "obligatoire"
        bigint target_id FK "obligatoire"
        bigint post_id FK "facultatif"
        enum reason "obligatoire"
        text comment "obligatoire"
        datetime created_at "obligatoire"
        datetime resolved_at "facultatif"
        bigint resolved_by_id FK "facultatif"
    }
    sessions {
        bigint id PK "obligatoire"
        bigint user_id FK "obligatoire"
        varchar token_hash UK "obligatoire"
        datetime created_at "obligatoire"
        datetime expires_at "obligatoire"
        datetime revoked_at "facultatif"
    }
    uploads {
        bigint id PK "obligatoire"
        varchar key UK "obligatoire"
        bigint owner_id FK "facultatif"
        int width "obligatoire"
        int height "obligatoire"
        bigint post_id FK "facultatif"
        smallint position "obligatoire"
        datetime created_at "obligatoire"
    }
    users {
        bigint id PK "obligatoire"
        varchar username UK "obligatoire"
        varchar email UK "obligatoire"
        varchar password_hash "obligatoire"
        varchar display_name "obligatoire"
        enum role "obligatoire"
        enum status "obligatoire"
        datetime created_at "obligatoire"
        datetime email_verified_at "facultatif"
        datetime suspended_at "facultatif"
        enum default_post_visibility "obligatoire"
        enum friends_list_audience "obligatoire"
        enum outings_audience "obligatoire"
        enum friend_requests_from "obligatoire"
        tinyint show_in_suggestions "obligatoire"
        varchar bio "obligatoire"
    }
    uploads |o..o{ communities : "banner_id"
    uploads |o..o{ communities : "icon_id"
    massifs |o..o{ communities : "massif_id"
    communities ||--o{ community_members : "community_id"
    users ||--o{ community_members : "user_id"
    communities ||--o{ community_refuges : "community_id"
    refuges ||--o{ community_refuges : "refuge_id"
    users ||..o{ email_tokens : "user_id"
    users ||..o{ friendships : "addressee_id"
    users ||..o{ friendships : "requester_id"
    users |o..o{ moderation_log : "actor_id"
    users ||..o{ outing_invitations : "invited_by_id"
    outings ||--o{ outing_invitations : "outing_id"
    users ||--o{ outing_invitations : "user_id"
    outings ||--o{ outing_participants : "outing_id"
    users ||--o{ outing_participants : "user_id"
    outings ||..o{ outing_stops : "outing_id"
    refuges |o..o{ outing_stops : "refuge_id"
    users ||..o{ outings : "organizer_id"
    posts ||--o{ post_likes : "post_id"
    users ||--o{ post_likes : "user_id"
    users ||..o{ posts : "author_id"
    communities |o..o{ posts : "community_id"
    refuges |o..o{ posts : "refuge_id"
    refuges ||..o{ refuge_photos : "refuge_id"
    uploads ||..o| refuge_photos : "upload_id"
    massifs |o..o{ refuges : "massif_id"
    posts |o..o{ reports : "post_id"
    users ||..o{ reports : "reporter_id"
    users |o..o{ reports : "resolved_by_id"
    users ||..o{ reports : "target_id"
    users ||..o{ sessions : "user_id"
    users |o..o{ uploads : "owner_id"
    posts |o..o{ uploads : "post_id"
```
