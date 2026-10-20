import type { Photo } from '../api/media'
import { cx } from '../lib/cx'
import styles from './PhotoGrid.module.css'

type PhotoGridProps = {
  photos: Photo[]
  /** Texte alternatif commun (les photos n'ont pas de légende). */
  alt: string
}

/**
 * Photos d'un post (écran 08) : une seule en pleine largeur, sinon deux par ligne
 * (la première en pleine largeur quand il y en a trois). Un clic ouvre l'original.
 */
export function PhotoGrid({ photos, alt }: PhotoGridProps) {
  if (photos.length === 0) return null
  return (
    <div className={cx(styles.grid, photos.length === 1 && styles.single, photos.length === 3 && styles.three)}>
      {photos.map((photo, index) => (
        <a key={photo.url} href={photo.url} target="_blank" rel="noreferrer" className={styles.item}>
          <img
            src={photo.url}
            width={photo.width}
            height={photo.height}
            alt={photos.length > 1 ? `${alt} (${index + 1} sur ${photos.length})` : alt}
            loading="lazy"
            className={styles.image}
          />
        </a>
      ))}
    </div>
  )
}
