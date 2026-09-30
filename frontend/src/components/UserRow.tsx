import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { cx } from '../lib/cx'
import { Avatar, type AvatarSize } from './Avatar'
import styles from './UserRow.module.css'

type UserRowProps = {
  name: string
  username: string
  /** Remplace « @pseudo » sous le nom (« 3 amis en commun »…). */
  meta?: ReactNode
  avatarSize?: AvatarSize
  /** Boutons alignés à droite (Accepter / Refuser, + Ajouter…). */
  actions?: ReactNode
  /** Version resserrée des écrans de modération (14 / 12 px). */
  compact?: boolean
}

export function UserRow({ name, username, meta, avatarSize = 'xl', actions, compact = false }: UserRowProps) {
  return (
    <div className={cx(styles.row, compact && styles.compact)}>
      <Avatar name={name} size={avatarSize} />
      <div className={styles.identity}>
        <Link to={`/u/${username}`} className={styles.name}>
          {name}
        </Link>
        <span className={styles.meta}>{meta ?? `@${username}`}</span>
      </div>
      {actions && <div className={styles.actions}>{actions}</div>}
    </div>
  )
}
