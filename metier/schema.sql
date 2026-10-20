SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `alembic_version`;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `communities`;
CREATE TABLE `communities` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `slug` varchar(80) NOT NULL,
  `name` varchar(80) NOT NULL,
  `description` text NOT NULL,
  `region` varchar(40) NOT NULL,
  `massif_id` bigint DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `banner_id` bigint DEFAULT NULL,
  `icon_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_communities_slug` (`slug`),
  KEY `ix_communities_massif_id` (`massif_id`),
  KEY `ix_communities_region` (`region`),
  KEY `fk_communities_banner_id_uploads` (`banner_id`),
  KEY `fk_communities_icon_id_uploads` (`icon_id`),
  CONSTRAINT `fk_communities_banner_id_uploads` FOREIGN KEY (`banner_id`) REFERENCES `uploads` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_communities_icon_id_uploads` FOREIGN KEY (`icon_id`) REFERENCES `uploads` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_communities_massif_id_massifs` FOREIGN KEY (`massif_id`) REFERENCES `massifs` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `community_members`;
CREATE TABLE `community_members` (
  `community_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `joined_at` datetime NOT NULL,
  PRIMARY KEY (`community_id`,`user_id`),
  KEY `ix_community_members_user_id` (`user_id`),
  CONSTRAINT `fk_community_members_community_id_communities` FOREIGN KEY (`community_id`) REFERENCES `communities` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_community_members_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `community_refuges`;
CREATE TABLE `community_refuges` (
  `community_id` bigint NOT NULL,
  `refuge_id` bigint NOT NULL,
  PRIMARY KEY (`community_id`,`refuge_id`),
  KEY `fk_community_refuges_refuge_id_refuges` (`refuge_id`),
  CONSTRAINT `fk_community_refuges_community_id_communities` FOREIGN KEY (`community_id`) REFERENCES `communities` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_community_refuges_refuge_id_refuges` FOREIGN KEY (`refuge_id`) REFERENCES `refuges` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `email_tokens`;
CREATE TABLE `email_tokens` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `purpose` enum('verify','reset') NOT NULL,
  `token_hash` varchar(64) NOT NULL,
  `email` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL,
  `expires_at` datetime NOT NULL,
  `used_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_email_tokens_token_hash` (`token_hash`),
  KEY `ix_email_tokens_user_id` (`user_id`),
  CONSTRAINT `fk_email_tokens_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `friendships`;
CREATE TABLE `friendships` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `requester_id` bigint NOT NULL,
  `addressee_id` bigint NOT NULL,
  `status` enum('pending','accepted','declined') NOT NULL,
  `created_at` datetime NOT NULL,
  `responded_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_friendships_requester_id` (`requester_id`,`addressee_id`),
  KEY `ix_friendships_addressee_id` (`addressee_id`),
  CONSTRAINT `fk_friendships_addressee_id_users` FOREIGN KEY (`addressee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_friendships_requester_id_users` FOREIGN KEY (`requester_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `massifs`;
CREATE TABLE `massifs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `external_id` int NOT NULL,
  `name` varchar(120) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_massifs_external_id` (`external_id`)
) ENGINE=InnoDB AUTO_INCREMENT=157 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `moderation_log`;
CREATE TABLE `moderation_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `actor_id` bigint DEFAULT NULL,
  `message` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_moderation_log_actor_id_users` (`actor_id`),
  KEY `ix_moderation_log_created_at` (`created_at`),
  CONSTRAINT `fk_moderation_log_actor_id_users` FOREIGN KEY (`actor_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `outing_invitations`;
CREATE TABLE `outing_invitations` (
  `outing_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `invited_by_id` bigint NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`outing_id`,`user_id`),
  KEY `fk_outing_invitations_invited_by_id_users` (`invited_by_id`),
  KEY `ix_outing_invitations_user_id` (`user_id`),
  CONSTRAINT `fk_outing_invitations_invited_by_id_users` FOREIGN KEY (`invited_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_outing_invitations_outing_id_outings` FOREIGN KEY (`outing_id`) REFERENCES `outings` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_outing_invitations_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `outing_participants`;
CREATE TABLE `outing_participants` (
  `outing_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `joined_at` datetime NOT NULL,
  PRIMARY KEY (`outing_id`,`user_id`),
  KEY `ix_outing_participants_user_id` (`user_id`),
  CONSTRAINT `fk_outing_participants_outing_id_outings` FOREIGN KEY (`outing_id`) REFERENCES `outings` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_outing_participants_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `outing_stops`;
CREATE TABLE `outing_stops` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `outing_id` bigint NOT NULL,
  `position` int NOT NULL,
  `refuge_id` bigint DEFAULT NULL,
  `name` varchar(200) NOT NULL,
  `latitude` decimal(9,6) NOT NULL,
  `longitude` decimal(9,6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_outing_stops_outing_id` (`outing_id`),
  KEY `ix_outing_stops_refuge_id` (`refuge_id`),
  CONSTRAINT `fk_outing_stops_outing_id_outings` FOREIGN KEY (`outing_id`) REFERENCES `outings` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_outing_stops_refuge_id_refuges` FOREIGN KEY (`refuge_id`) REFERENCES `refuges` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `outings`;
CREATE TABLE `outings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(80) NOT NULL,
  `organizer_id` bigint NOT NULL,
  `starts_at` datetime NOT NULL,
  `max_participants` int NOT NULL,
  `visibility` enum('public','invitation') NOT NULL,
  `path` json NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_outings_organizer_id` (`organizer_id`),
  KEY `ix_outings_starts_at` (`starts_at`),
  CONSTRAINT `fk_outings_organizer_id_users` FOREIGN KEY (`organizer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `post_likes`;
CREATE TABLE `post_likes` (
  `post_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`post_id`,`user_id`),
  KEY `fk_post_likes_user_id_users` (`user_id`),
  CONSTRAINT `fk_post_likes_post_id_posts` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_post_likes_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `posts`;
CREATE TABLE `posts` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `author_id` bigint NOT NULL,
  `community_id` bigint DEFAULT NULL,
  `body` text NOT NULL,
  `visibility` enum('public','friends') NOT NULL,
  `created_at` datetime NOT NULL,
  `refuge_id` bigint DEFAULT NULL,
  `path` json DEFAULT NULL,
  `distance_m` int DEFAULT NULL,
  `elevation_gain_m` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_posts_author_id` (`author_id`),
  KEY `ix_posts_community_created` (`community_id`,`created_at`),
  KEY `ix_posts_refuge_id` (`refuge_id`),
  CONSTRAINT `fk_posts_author_id_users` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_posts_community_id_communities` FOREIGN KEY (`community_id`) REFERENCES `communities` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_posts_refuge_id_refuges` FOREIGN KEY (`refuge_id`) REFERENCES `refuges` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `refuge_photos`;
CREATE TABLE `refuge_photos` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `refuge_id` bigint NOT NULL,
  `upload_id` bigint NOT NULL,
  `external_id` int NOT NULL,
  `author` varchar(120) NOT NULL,
  `caption` varchar(300) NOT NULL,
  `taken_at` datetime DEFAULT NULL,
  `position` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_refuge_photos_external_id` (`external_id`),
  UNIQUE KEY `uq_refuge_photos_upload_id` (`upload_id`),
  KEY `ix_refuge_photos_refuge_id` (`refuge_id`),
  CONSTRAINT `fk_refuge_photos_refuge_id_refuges` FOREIGN KEY (`refuge_id`) REFERENCES `refuges` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_refuge_photos_upload_id_uploads` FOREIGN KEY (`upload_id`) REFERENCES `uploads` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `refuges`;
CREATE TABLE `refuges` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `external_id` int NOT NULL,
  `name` varchar(200) NOT NULL,
  `kind` enum('unguarded_hut','gite','guarded_hut') NOT NULL,
  `latitude` decimal(9,6) NOT NULL,
  `longitude` decimal(9,6) NOT NULL,
  `altitude` int DEFAULT NULL,
  `capacity` int DEFAULT NULL,
  `massif_id` bigint DEFAULT NULL,
  `state` varchar(80) DEFAULT NULL,
  `access` text,
  `remarks` text,
  `owner_info` text,
  `source_url` varchar(255) DEFAULT NULL,
  `source_updated_at` datetime DEFAULT NULL,
  `imported_at` datetime NOT NULL,
  `photos_checked_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_refuges_external_id` (`external_id`),
  KEY `ix_refuges_lat_lng` (`latitude`,`longitude`),
  KEY `ix_refuges_massif_id` (`massif_id`),
  KEY `ix_refuges_name` (`name`),
  CONSTRAINT `fk_refuges_massif_id_massifs` FOREIGN KEY (`massif_id`) REFERENCES `massifs` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=4653 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `reports`;
CREATE TABLE `reports` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `reporter_id` bigint NOT NULL,
  `target_id` bigint NOT NULL,
  `post_id` bigint DEFAULT NULL,
  `reason` enum('insulting','spam','fake_profile','other') NOT NULL,
  `comment` text NOT NULL,
  `created_at` datetime NOT NULL,
  `resolved_at` datetime DEFAULT NULL,
  `resolved_by_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_reports_post_id_posts` (`post_id`),
  KEY `fk_reports_reporter_id_users` (`reporter_id`),
  KEY `fk_reports_resolved_by_id_users` (`resolved_by_id`),
  KEY `ix_reports_resolved_at` (`resolved_at`),
  KEY `ix_reports_target_id` (`target_id`),
  CONSTRAINT `fk_reports_post_id_posts` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_reports_reporter_id_users` FOREIGN KEY (`reporter_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_reports_resolved_by_id_users` FOREIGN KEY (`resolved_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_reports_target_id_users` FOREIGN KEY (`target_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `sessions`;
CREATE TABLE `sessions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `token_hash` varchar(64) NOT NULL,
  `created_at` datetime NOT NULL,
  `expires_at` datetime NOT NULL,
  `revoked_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sessions_token_hash` (`token_hash`),
  KEY `ix_sessions_user_id` (`user_id`),
  CONSTRAINT `fk_sessions_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `uploads`;
CREATE TABLE `uploads` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `key` varchar(32) NOT NULL,
  `owner_id` bigint DEFAULT NULL,
  `width` int NOT NULL,
  `height` int NOT NULL,
  `post_id` bigint DEFAULT NULL,
  `position` smallint NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_uploads_key` (`key`),
  KEY `ix_uploads_owner_id` (`owner_id`),
  KEY `ix_uploads_post_id` (`post_id`),
  CONSTRAINT `fk_uploads_owner_id_users` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_uploads_post_id_posts` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(30) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `display_name` varchar(60) NOT NULL,
  `role` enum('user','moderator','super_admin') NOT NULL,
  `status` enum('pending_email','active','suspended') NOT NULL,
  `created_at` datetime NOT NULL,
  `email_verified_at` datetime DEFAULT NULL,
  `suspended_at` datetime DEFAULT NULL,
  `default_post_visibility` enum('public','friends') NOT NULL DEFAULT 'public',
  `friends_list_audience` enum('everyone','friends','me') NOT NULL DEFAULT 'friends',
  `outings_audience` enum('everyone','friends','me') NOT NULL DEFAULT 'everyone',
  `friend_requests_from` enum('everyone','communities') NOT NULL DEFAULT 'everyone',
  `show_in_suggestions` tinyint(1) NOT NULL DEFAULT '1',
  `bio` varchar(300) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`),
  UNIQUE KEY `uq_users_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;
