import { Link } from 'react-router'
import styles from './PostTile.module.css'
import { VisibilityBadge, type Visibility } from './VisibilityBadge'

type PostTileProps = {
  post: { body: string; visibility: Visibility; community: { slug: string } | null }
  /** Badge Public / Amis posé sur la vignette (masqué quand tout est public, écran 06). */
  showBadge?: boolean
}

/**
 * Vignette de la grille « Publications » d'un profil (écrans 05, 06). Les posts n'ont pas
 * encore de photo ni de chemin : la vignette montre le début du texte.
 */
export function PostTile({ post, showBadge = true }: PostTileProps) {
  const content = (
    <>
      {showBadge && (
        <span className={styles.badge}>
          <VisibilityBadge visibility={post.visibility} variant="overlay" />
        </span>
      )}
      <span className={styles.text}>{post.body}</span>
    </>
  )
  // Un post de communauté mène au fil de la communauté ; un post de profil n'a pas de page.
  if (post.community) {
    return (
      <Link to={`/communautes/${post.community.slug}`} className={styles.tile}>
        {content}
      </Link>
    )
  }
  return <div className={styles.tile}>{content}</div>
}
