import { Check } from 'lucide-react'
import { Link } from 'react-router'
import { formatCount } from '../lib/format'
import { Button } from './Button'
import styles from './CommunityCard.module.css'
import { Tag } from './Tag'

type CommunityCardProps = {
  community: {
    slug: string
    name: string
    region: string
    member_count: number
    post_count: number
    is_member: boolean
  }
  /** Rejoindre ou quitter ; absent : pas de bouton. */
  onToggleMembership?: () => void
  /** Requête en cours : bouton désactivé. */
  busy?: boolean
}

/** Carte de l'écran 07 : image, nom, compteurs, région et « Rejoindre » / « Inscrit ✓ ». */
export function CommunityCard({ community, onToggleMembership, busy = false }: CommunityCardProps) {
  return (
    <article className={styles.card}>
      {/* Pas encore de bannière : zone réservée, comme dans la maquette. */}
      <div className={styles.image} aria-hidden />
      <h2 className={styles.name}>
        <Link to={`/communautes/${community.slug}`} className={styles.link}>
          {community.name}
        </Link>
      </h2>
      <p className={styles.meta}>
        {formatCount(community.member_count, 'membre')} · {formatCount(community.post_count, 'post')}
      </p>
      <div className={styles.footer}>
        <Tag>{community.region}</Tag>
        {onToggleMembership &&
          (community.is_member ? (
            <Button
              size="sm"
              variant="secondary"
              disabled={busy}
              onClick={onToggleMembership}
              title="Quitter la communauté"
              icon={<Check aria-hidden size={14} />}
              className={styles.joined}
            >
              Inscrit
            </Button>
          ) : (
            <Button size="sm" disabled={busy} onClick={onToggleMembership}>
              Rejoindre
            </Button>
          ))}
      </div>
    </article>
  )
}
