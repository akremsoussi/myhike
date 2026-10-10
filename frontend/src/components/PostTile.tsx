import { Link } from 'react-router'
import type { Photo } from '../api/media'
import { cx } from '../lib/cx'
import { PathPreview } from './PathPreview'
import styles from './PostTile.module.css'
import { VisibilityBadge, type Visibility } from './VisibilityBadge'

type PostTileProps = {
  post: {
    body: string
    photos?: Photo[]
    path?: [number, number][] | null
    visibility: Visibility
    community: { slug: string } | null
  }
  /** Badge Public / Amis posé sur la vignette (masqué quand tout est public, écran 06). */
  showBadge?: boolean
}

/**
 * Vignette de la grille « Publications » d'un profil (écrans 05, 06) : la première photo,
 * sinon le chemin, sinon le début du texte.
 */
export function PostTile({ post, showBadge = true }: PostTileProps) {
  const photo = post.photos?.[0]
  const path = photo ? null : post.path
  const content = (
    <>
      {photo && <img src={photo.url} alt="" loading="lazy" className={styles.photo} />}
      {path && <PathPreview points={path} className={styles.path} />}
      {showBadge && (
        <span className={styles.badge}>
          <VisibilityBadge visibility={post.visibility} variant="overlay" />
        </span>
      )}
      {!photo && !path && <span className={styles.text}>{post.body}</span>}
    </>
  )
  const label = photo ? post.body || 'Photo' : path ? post.body || 'Chemin' : undefined
  // Un post de communauté mène au fil de la communauté ; un post de profil n'a pas de page.
  if (post.community) {
    return (
      <Link to={`/communautes/${post.community.slug}`} className={cx(styles.tile, (photo || path) && styles.withPhoto)} aria-label={label}>
        {content}
      </Link>
    )
  }
  return (
    <div className={cx(styles.tile, (photo || path) && styles.withPhoto)} role={photo || path ? 'img' : undefined} aria-label={label}>
      {content}
    </div>
  )
}
