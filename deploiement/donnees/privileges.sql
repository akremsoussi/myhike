-- Initialisation de la base et restriction stricte des privilèges
-- Seule l'adresse IP de vm-metier (10.10.10.20) est autorisée à se connecter.
-- Équivalent MySQL de la ligne pg_hba.conf sous PostgreSQL.

CREATE DATABASE IF NOT EXISTS refuges CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Création de l'utilisateur applicatif restreint à l'IP du serveur métier
CREATE USER IF NOT EXISTS 'refuges'@'10.10.10.20' IDENTIFIED BY 'refuges';

-- Attribution des droits sur la base
GRANT ALL PRIVILEGES ON refuges.* TO 'refuges'@'10.10.10.20';

FLUSH PRIVILEGES;
