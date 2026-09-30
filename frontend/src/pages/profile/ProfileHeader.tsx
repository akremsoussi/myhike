import type { ReactNode } from 'react'
import type { Profile } from '../../api/users'
import { Avatar, StatBlock } from '../../components'
import styles from './profile.module.css'

type ProfileHeaderProps = {
  profile: Profile
  /** Complément après « @pseudo » (« membre depuis 2025 », « Ami depuis mars 2026 »). */
  meta: string
  /** Boutons à droite (Modifier le profil, + Ajouter en ami…). */
  actions: ReactNode
}

/** En-tête des écrans 05 et 06 : avatar, identité, statistiques et actions. */
export function ProfileHeader({ profile, meta, actions }: ProfileHeaderProps) {
  return (
    <section className={styles.header}>
      <Avatar name={profile.user.display_name} size="6xl" />
      <div className={styles.identity}>
        <h1 className={styles.name}>{profile.user.display_name}</h1>
        <p className={styles.meta}>
          @{profile.user.username} · {meta}
        </p>
      </div>
      <div className={styles.stats}>
        {profile.outing_count !== null && <StatBlock value={profile.outing_count} label="Sorties" />}
        <StatBlock value={profile.post_count} label="Posts" />
        <StatBlock value={profile.community_count} label="Communautés" />
        {profile.friend_count !== null && <StatBlock value={profile.friend_count} label="Amis" />}
      </div>
      <div className={styles.actions}>{actions}</div>
    </section>
  )
}
