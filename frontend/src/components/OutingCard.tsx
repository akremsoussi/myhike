import { cx } from '../lib/cx'
import { formatOutingDate, shortName } from '../lib/format'
import { AvatarGroup } from './AvatarGroup'
import { ButtonLink } from './ButtonLink'
import styles from './OutingCard.module.css'
import { PathPreview } from './PathPreview'
import { StatusBadge } from './StatusBadge'

type OutingCardProps = {
  outing: {
    id: number
    title: string
    starts_at: string
    organizer: { username: string; display_name: string }
    status: 'open' | 'full'
    participant_count: number
    max_participants: number
    stop_count: number
    participants_preview: { display_name: string }[]
    preview: [number, number][]
  }
  /** Pseudo du visiteur : « organisée par moi » quand c'est lui l'organisateur. */
  viewerUsername?: string
  /** Sans vignette : sections « sorties à venir » des profils (écrans 05 et 06). */
  compact?: boolean
}

/** Carte d'une sortie (écran 10, profils). */
export function OutingCard({ outing, viewerUsername, compact = false }: OutingCardProps) {
  const organizer =
    outing.organizer.username === viewerUsername ? 'moi' : shortName(outing.organizer.display_name)
  const meta = [
    formatOutingDate(outing.starts_at),
    compact ? `organisée par ${organizer}` : `par ${organizer}`,
    !compact && `${outing.stop_count} point${outing.stop_count > 1 ? 's' : ''} de stop`,
  ]
  return (
    <article className={cx(styles.card, compact && styles.compact)}>
      {!compact && <PathPreview points={outing.preview} />}
      <div className={styles.titleRow}>
        <h3 className={styles.title}>{outing.title}</h3>
        {outing.status === 'full' ? (
          <StatusBadge tone="accent">Complète</StatusBadge>
        ) : (
          <StatusBadge tone="success">Ouverte</StatusBadge>
        )}
      </div>
      <p className={styles.meta}>{meta.filter(Boolean).join(' · ')}</p>
      <div className={styles.footer}>
        <AvatarGroup names={outing.participants_preview.map((p) => p.display_name)} />
        <span className={styles.participants}>
          {outing.participant_count}/{outing.max_participants} participants
        </span>
        <ButtonLink to={`/sorties/${outing.id}`} size="sm" variant="secondary">
          Voir
        </ButtonLink>
      </div>
    </article>
  )
}
