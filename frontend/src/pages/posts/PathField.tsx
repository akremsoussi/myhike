import { Eraser, Pencil, Undo2 } from 'lucide-react'
import { lazy, Suspense, useRef, useState, type ChangeEvent } from 'react'
import type { PathPoint } from '../../api/communities'
import type { LatLng } from '../../api/outings'
import { Button } from '../../components'
import { cx } from '../../lib/cx'
import { formatAltitude, formatDistance } from '../../lib/format'
import { downsample, elevationGainM, pathLengthM } from '../../lib/geo'
import { parseGpx } from '../../lib/gpx'
import styles from './PathField.module.css'

// Leaflet n'est chargé qu'en ouvrant le formulaire de publication.
const OutingMap = lazy(async () => ({ default: (await import('../outings/OutingMap')).OutingMap }))

/** Même limite que l'API : un GPX plus détaillé est simplifié avant l'envoi. */
export const MAX_PATH_POINTS = 2000
const GPX_MAX_BYTES = 5 * 1024 * 1024

type PathFieldProps = {
  path: PathPoint[]
  onChange: (path: PathPoint[]) => void
  error?: string
}

/** « Chemin (optionnel) » de l'écran 09 : tracé à la main sur la carte, ou import d'un GPX. */
export function PathField({ path, onChange, error }: PathFieldProps) {
  const [drawing, setDrawing] = useState(false)
  const [importError, setImportError] = useState<string | null>(null)
  // Recadre la carte après un import, pas à chaque point tracé.
  const [fitKey, setFitKey] = useState('initial')
  const input = useRef<HTMLInputElement>(null)
  const points = path.map(([lat, lng]): LatLng => [lat, lng])
  const gain = elevationGainM(path)

  function addPoint(point: LatLng) {
    if (path.length >= MAX_PATH_POINTS) return
    // Un point tracé n'a pas d'altitude : le dénivelé d'un GPX complété n'est plus calculable.
    onChange([...path, point])
  }

  async function importGpx(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = '' // pouvoir choisir à nouveau le même fichier
    if (!file) return
    setImportError(null)
    if (file.size > GPX_MAX_BYTES) {
      setImportError('Fichier GPX trop lourd (5 Mo max.).')
      return
    }
    let text: string
    try {
      text = await file.text()
    } catch {
      setImportError('Ce fichier GPX n’a pas pu être lu.')
      return
    }
    try {
      onChange(downsample(parseGpx(text), MAX_PATH_POINTS))
      setDrawing(false)
      setFitKey(`gpx-${Date.now()}`)
    } catch (err) {
      // Messages de parseGpx, déjà en français.
      setImportError(err instanceof Error ? err.message : 'Ce fichier GPX n’a pas pu être lu.')
    }
  }

  const message = importError ?? error
  return (
    <div className={styles.field}>
      <div className={styles.mapBox}>
        <Suspense fallback={null}>
          <OutingMap stops={[]} path={points} onMapClick={drawing ? addPoint : undefined} fitKey={fitKey} />
        </Suspense>
        <p className={styles.hint}>
          {drawing ? 'Cliquez sur la carte pour tracer le chemin' : path.length > 0 ? 'Chemin du post' : 'Tracez ou importez votre chemin'}
        </p>
        <div className={styles.tools} role="toolbar" aria-label="Outils de tracé">
          <button
            type="button"
            className={cx(styles.tool, drawing && styles.toolActive)}
            aria-pressed={drawing}
            title="Tracer le chemin"
            onClick={() => setDrawing(!drawing)}
          >
            <Pencil aria-hidden size={16} />
          </button>
          <button type="button" className={styles.tool} title="Annuler le dernier point" disabled={path.length === 0} onClick={() => onChange(path.slice(0, -1))}>
            <Undo2 aria-hidden size={16} />
          </button>
          <button type="button" className={styles.tool} title="Effacer le chemin" disabled={path.length === 0} onClick={() => onChange([])}>
            <Eraser aria-hidden size={16} />
          </button>
        </div>
      </div>
      <div className={styles.buttons}>
        <Button variant={drawing ? 'primary' : 'secondary'} fullWidth aria-pressed={drawing} onClick={() => setDrawing(!drawing)}>
          {drawing ? 'Terminer le tracé' : 'Tracer sur la carte'}
        </Button>
        <Button variant="secondary" fullWidth onClick={() => input.current?.click()}>
          Importer un GPX
        </Button>
        <input ref={input} type="file" accept=".gpx,application/gpx+xml" className={styles.fileInput} tabIndex={-1} aria-hidden onChange={(event) => void importGpx(event)} />
      </div>
      {message ? (
        <p className={styles.error} role="alert">
          {message}
        </p>
      ) : (
        <p className={styles.stats}>
          {path.length >= 2
            ? [formatDistance(pathLengthM(path)), gain !== null && `D+ ${formatAltitude(gain)}`].filter(Boolean).join(' · ')
            : path.length === 1
              ? 'Ajoutez au moins un deuxième point.'
              : 'Le dénivelé est calculé à partir des altitudes d’un GPX.'}
        </p>
      )}
    </div>
  )
}
