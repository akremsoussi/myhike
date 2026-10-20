import { Flag, Heart, MapPin, MoreHorizontal, Route, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { cx } from '../lib/cx'
import { formatAltitude, formatDistance, formatNumber, formatRelative } from '../lib/format'
import type { Photo } from '../api/media'
import { Avatar } from './Avatar'
import { PathPreview } from './PathPreview'
import { PhotoGrid } from './PhotoGrid'
import { StatusBadge } from './StatusBadge'
import styles from './PostCard.module.css'
import { VisibilityBadge, type Visibility } from './VisibilityBadge'

type PostCardProps = {
  post: {
    author: { username: string; display_name: string }
    /** Affichée sous l'auteur, hors du fil de cette communauté (profil). */
    community?: { slug: string; name: string } | null
    /** Refuge dont parle le post, affiché sous l'auteur (masqué dans les posts liés au refuge). */
    refuge?: { id: number; name: string } | null
    body: string
    photos?: Photo[]
    /** Chemin simplifié [latitude, longitude], avec sa distance et son dénivelé. */
    path?: [number, number][] | null
    distance_m?: number | null
    elevation_gain_m?: number | null
    visibility: Visibility
    created_at: string
    like_count: number
    liked: boolean
    can_delete: boolean
  }
  onToggleLike?: () => void
  onDelete?: () => void
  /** « Signaler » dans le menu « ⋯ » (posts des autres). */
  onReport?: () => void
  /** Requête en cours : actions désactivées. */
  busy?: boolean
}

/** Post d'un fil (écran 08) : auteur, date, visibilité, texte, photos, chemin et actions. */
export function PostCard({ post, onToggleLike, onDelete, onReport, busy = false }: PostCardProps) {
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const profileUrl = `/u/${post.author.username}`
  const canDelete = post.can_delete && onDelete !== undefined

  // Fermer le menu « ⋯ » au clic ailleurs.
  useEffect(() => {
    if (!menuOpen) return
    function close(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [menuOpen])

  return (
    <article className={styles.card}>
      <header className={styles.header}>
        <Avatar name={post.author.display_name} size="2xl" />
        <div className={styles.identity}>
          <Link to={profileUrl} className={styles.author}>
            {post.author.display_name}
          </Link>
          <p className={styles.meta}>
            <time dateTime={post.created_at} title={new Date(post.created_at).toLocaleString('fr-FR')}>
              {formatRelative(post.created_at)}
            </time>
            <span aria-hidden>·</span>
            <VisibilityBadge visibility={post.visibility} variant="meta" />
            {post.community && (
              <>
                <span aria-hidden>·</span>
                <Link to={`/communautes/${post.community.slug}`} className={styles.community}>
                  {post.community.name}
                </Link>
              </>
            )}
            {post.refuge && (
              <>
                <span aria-hidden>·</span>
                <Link to={`/refuges/${post.refuge.id}`} className={styles.community}>
                  <MapPin aria-hidden size={13} />
                  {post.refuge.name}
                </Link>
              </>
            )}
          </p>
        </div>
        {(canDelete || onReport) && (
          <div className={styles.menu} ref={menuRef}>
            <button
              type="button"
              className={styles.menuButton}
              aria-label="Actions"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              <MoreHorizontal aria-hidden size={20} />
            </button>
            {menuOpen && (
              <div className={styles.menuList} role="menu">
                {onReport && (
                  <button
                    type="button"
                    role="menuitem"
                    className={styles.menuItem}
                    onClick={() => {
                      setMenuOpen(false)
                      onReport()
                    }}
                  >
                    <Flag aria-hidden size={16} />
                    Signaler
                  </button>
                )}
                {canDelete && (
                  <button
                    type="button"
                    role="menuitem"
                    className={`${styles.menuItem} ${styles.danger}`}
                    disabled={busy}
                    onClick={() => {
                      setMenuOpen(false)
                      onDelete?.()
                    }}
                  >
                    <Trash2 aria-hidden size={16} />
                    Supprimer
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </header>

      {post.body && <p className={styles.body}>{post.body}</p>}
      {post.photos && <PhotoGrid photos={post.photos} alt={`Photo de ${post.author.display_name}`} />}
      {post.path && (
        <div className={styles.path}>
          <PathPreview points={post.path} className={styles.pathPreview} />
          <p className={styles.pathStats}>
            <StatusBadge tone="accent" icon={<Route aria-hidden size={13} />}>
              Chemin
            </StatusBadge>
            {post.distance_m !== null && post.distance_m !== undefined && <span>{formatDistance(post.distance_m)}</span>}
            {post.elevation_gain_m !== null && post.elevation_gain_m !== undefined && (
              <span title="Dénivelé positif">D+ {formatAltitude(post.elevation_gain_m)}</span>
            )}
          </p>
        </div>
      )}

      <footer className={styles.actions}>
        <button
          type="button"
          className={cx(styles.action, post.liked && styles.liked)}
          aria-pressed={post.liked}
          aria-label={post.liked ? 'Je n’aime plus' : 'J’aime'}
          disabled={busy || !onToggleLike}
          onClick={onToggleLike}
        >
          <Heart aria-hidden size={16} fill={post.liked ? 'currentColor' : 'none'} />
          {formatNumber(post.like_count)}
        </button>
        <Link to={profileUrl} className={styles.profileLink}>
          Voir le profil
        </Link>
      </footer>
    </article>
  )
}
