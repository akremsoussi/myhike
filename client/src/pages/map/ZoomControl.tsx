import { Minus, Plus } from 'lucide-react'
import { useMap } from 'react-leaflet'
import styles from './MapPage.module.css'

/** Boutons + / − en haut à droite de la carte (écran 03). */
export function ZoomControl() {
  const map = useMap()
  return (
    <div className={styles.zoom}>
      <button type="button" className={styles.zoomButton} onClick={() => map.zoomIn()} aria-label="Zoomer">
        <Plus aria-hidden size={18} />
      </button>
      <button type="button" className={styles.zoomButton} onClick={() => map.zoomOut()} aria-label="Dézoomer">
        <Minus aria-hidden size={18} />
      </button>
    </div>
  )
}
