import type { ReactNode } from 'react'
import { cx } from '../lib/cx'
import styles from './StatusBadge.module.css'

export type StatusTone = 'success' | 'accent' | 'danger' | 'neutral' | 'pending'

type StatusBadgeProps = {
  /**
   * success : « Ouverte » · accent : « Complète », « Chemin » · danger : « Signalé »
   * neutral : « Non gardé », « Suspendu » · pending : « En attente »
   */
  tone: StatusTone
  /** « xs » : badge de rôle en capitales (« MODÉRATEUR ») · « count » : compteur (« 2 »), comme dans les onglets. */
  size?: 'md' | 'xs' | 'count'
  icon?: ReactNode
  children: ReactNode
}

export function StatusBadge({ tone, size = 'md', icon, children }: StatusBadgeProps) {
  return (
    <span className={cx(styles.badge, styles[tone], styles[size])}>
      {icon}
      {children}
    </span>
  )
}
