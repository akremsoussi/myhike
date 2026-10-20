import { cx } from '../lib/cx'
import styles from './PathPreview.module.css'

const WIDTH = 340
const HEIGHT = 110
const PADDING = 14

type PathPreviewProps = {
  /** [latitude, longitude] dans l'ordre du chemin. */
  points: [number, number][]
  /** Pour changer la hauteur (110 px par défaut). */
  className?: string
}

/**
 * Vignette d'une sortie (écran 10) ou du chemin d'un post (écran 08) : le tracé en orange
 * sur le fond de carte, sans tuiles.
 * Projection équirectangulaire corrigée par la latitude, suffisante à cette échelle.
 */
export function PathPreview({ points, className }: PathPreviewProps) {
  let content = null
  if (points.length > 0) {
    const cos = Math.cos((points[0][0] * Math.PI) / 180)
    const xs = points.map(([, lng]) => lng * cos)
    const ys = points.map(([lat]) => -lat)
    const minX = Math.min(...xs)
    const minY = Math.min(...ys)
    const spanX = Math.max(...xs) - minX || 1e-9
    const spanY = Math.max(...ys) - minY || 1e-9
    const scale = Math.min((WIDTH - 2 * PADDING) / spanX, (HEIGHT - 2 * PADDING) / spanY)
    // Centre le tracé dans la vignette.
    const offsetX = (WIDTH - spanX * scale) / 2
    const offsetY = (HEIGHT - spanY * scale) / 2
    const projected = xs.map((x, i) => [offsetX + (x - minX) * scale, offsetY + (ys[i] - minY) * scale])
    content =
      projected.length === 1 ? (
        <circle className={styles.dot} cx={projected[0][0]} cy={projected[0][1]} r={5} />
      ) : (
        <polyline className={styles.path} points={projected.map(([x, y]) => `${x},${y}`).join(' ')} />
      )
  }
  return (
    <svg className={cx(styles.preview, className)} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} preserveAspectRatio="xMidYMid meet" aria-hidden>
      {content}
    </svg>
  )
}
