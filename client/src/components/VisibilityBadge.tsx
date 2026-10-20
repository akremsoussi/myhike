import { Globe, Lock } from 'lucide-react'
import { cx } from '../lib/cx'
import styles from './VisibilityBadge.module.css'

export type Visibility = 'public' | 'friends'

type VisibilityBadgeProps = {
  visibility: Visibility
  /** « overlay » : posé sur une photo ou un chemin · « meta » : en-tête d'un post (13 px Regular). */
  variant?: 'inline' | 'meta' | 'overlay'
}

const LABELS: Record<Visibility, string> = { public: 'Public', friends: 'Amis' }

/** Globe = Public, cadenas = Amis uniquement. */
export function VisibilityBadge({ visibility, variant = 'inline' }: VisibilityBadgeProps) {
  const Icon = visibility === 'public' ? Globe : Lock
  return (
    <span className={cx(styles.badge, styles[variant])}>
      <Icon aria-hidden size={12} strokeWidth={2.25} />
      {LABELS[visibility]}
    </span>
  )
}
