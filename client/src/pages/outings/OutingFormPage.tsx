import { ArrowLeft, Eraser, GripVertical, MapPin, Pencil, Plus, Search, Undo2, X } from 'lucide-react'
import { lazy, Suspense, useEffect, useState, type DragEvent, type FormEvent, type KeyboardEvent } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'
import { outingsApi, type LatLng, type OutingDetail, type OutingVisibility, type StopInput } from '../../api/outings'
import { refugesApi, type RefugeSummary } from '../../api/refuges'
import { Button, Chip, Input, Notice, StopNumber } from '../../components'
import { ApiError } from '../../lib/api'
import { cx } from '../../lib/cx'
import { formatAltitude } from '../../lib/format'
import styles from './OutingFormPage.module.css'

const OutingMap = lazy(async () => ({ default: (await import('./OutingMap')).OutingMap }))

const SEARCH_LIMIT = 8

type FormStop = {
  key: string
  refuge_id: number | null
  name: string
  latitude: number
  longitude: number
  altitude: number | null
}

/** Mode de la carte : rien, tracé du chemin, ou placement d'un point libre. */
type MapMode = 'idle' | 'draw' | 'free'

const HINTS: Record<MapMode, string> = {
  idle: 'Cliquez sur le crayon pour tracer le chemin, ou ajoutez des points de stop',
  draw: 'Cliquez sur la carte pour tracer le chemin',
  free: 'Cliquez sur la carte pour placer le point de stop',
}

let nextKey = 0
const newKey = () => `stop-${nextKey++}`

function fromRefuge(refuge: RefugeSummary): FormStop {
  return {
    key: newKey(),
    refuge_id: refuge.id,
    name: refuge.name,
    latitude: refuge.latitude,
    longitude: refuge.longitude,
    altitude: refuge.altitude,
  }
}

/** « 2026-10-04 » et « 07:30 » en heure locale. */
function splitLocal(iso: string): { date: string; time: string } {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return { date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`, time: `${pad(d.getHours())}:${pad(d.getMinutes())}` }
}

/** Écran 12 · Créer (`/sorties/nouvelle?refuge=…`) ou modifier (`/sorties/:id/modifier`) une sortie. */
export function OutingFormPage() {
  const { id } = useParams()
  return <OutingForm key={id ?? 'new'} outingId={id ? Number(id) : null} />
}

function OutingForm({ outingId }: { outingId: number | null }) {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const editing = outingId !== null

  const [title, setTitle] = useState('')
  const [date, setDate] = useState('')
  const [time, setTime] = useState('')
  const [places, setPlaces] = useState('8')
  const [visibility, setVisibility] = useState<OutingVisibility>('public')
  const [stops, setStops] = useState<FormStop[]>([])
  const [path, setPath] = useState<LatLng[]>([])
  const [mode, setMode] = useState<MapMode>('idle')
  const [fitKey, setFitKey] = useState('initial')
  const [adding, setAdding] = useState(false)
  const [loaded, setLoaded] = useState(!editing)

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [dragIndex, setDragIndex] = useState<number | null>(null)

  // Modification : on part de la sortie existante.
  useEffect(() => {
    if (outingId === null) return
    outingsApi
      .get(outingId)
      .then((outing: OutingDetail) => {
        if (!outing.is_organizer) {
          navigate(`/sorties/${outingId}`, { replace: true })
          return
        }
        const { date: d, time: t } = splitLocal(outing.starts_at)
        setTitle(outing.title)
        setDate(d)
        setTime(t)
        setPlaces(String(outing.max_participants))
        setVisibility(outing.visibility)
        setStops(outing.stops.map((s) => ({ key: newKey(), ...s })))
        setPath(outing.path)
        setFitKey(`outing-${outing.id}`)
        setLoaded(true)
      })
      .catch((err: unknown) => setFormError(err instanceof ApiError ? err.message : 'La sortie n’a pas pu être chargée.'))
  }, [outingId, navigate])

  // Création depuis un refuge (« Créer une sortie ici ») : il devient le premier point.
  const refugeParam = params.get('refuge')
  useEffect(() => {
    if (editing || !refugeParam) return
    refugesApi
      .get(Number(refugeParam))
      .then((refuge) => {
        setStops((current) => (current.length ? current : [fromRefuge(refuge)]))
        setFitKey(`refuge-${refuge.id}`)
      })
      .catch(() => undefined)
  }, [editing, refugeParam])

  function addStop(stop: FormStop) {
    setStops((current) => [...current, stop])
    setAdding(false)
    setErrors((current) => {
      const next = { ...current }
      delete next.stops
      return next
    })
  }

  function handleMapClick(point: LatLng) {
    if (mode === 'draw') setPath((current) => [...current, point])
    if (mode === 'free') {
      addStop({ key: newKey(), refuge_id: null, name: `Point libre ${stops.filter((s) => !s.refuge_id).length + 1}`, latitude: point[0], longitude: point[1], altitude: null })
      setMode('idle')
    }
  }

  function move(from: number, to: number) {
    if (to < 0 || to >= stops.length || from === to) return
    setStops((current) => {
      const next = [...current]
      const [item] = next.splice(from, 1)
      next.splice(to, 0, item)
      return next
    })
  }

  function onHandleKey(event: KeyboardEvent, index: number) {
    if (event.key === 'ArrowUp') move(index, index - 1)
    else if (event.key === 'ArrowDown') move(index, index + 1)
    else return
    event.preventDefault()
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    const local: Record<string, string> = {}
    if (title.trim().length < 3) local.title = '3 à 80 caractères.'
    if (!date || !time) local.starts_at = 'Choisissez une date et une heure.'
    if (stops.length === 0) local.stops = 'Ajoutez au moins un point de stop.'
    if (Object.keys(local).length) {
      setErrors(local)
      return
    }
    const body = {
      title,
      // Heure locale du navigateur, envoyée avec son fuseau (UTC).
      starts_at: new Date(`${date}T${time}`).toISOString(),
      max_participants: Number(places),
      visibility,
      stops: stops.map((s): StopInput => (s.refuge_id ? { refuge_id: s.refuge_id } : { name: s.name, latitude: s.latitude, longitude: s.longitude })),
      path,
    }
    setSubmitting(true)
    setErrors({})
    setFormError(null)
    try {
      const saved = outingId !== null ? await outingsApi.update(outingId, body) : await outingsApi.create(body)
      navigate(`/sorties/${saved.id}`)
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors(err.fields)
        setFormError(err.message)
      } else {
        setFormError('La sortie n’a pas pu être enregistrée.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function remove() {
    if (outingId === null || !window.confirm('Supprimer cette sortie ? Les participants ne la verront plus.')) return
    try {
      await outingsApi.remove(outingId)
      navigate('/sorties')
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'La sortie n’a pas pu être supprimée.')
    }
  }

  const backUrl = editing ? `/sorties/${outingId}` : '/sorties'

  return (
    <div className={styles.page}>
      <Link to={backUrl} className={styles.back}>
        <ArrowLeft aria-hidden size={14} />
        {editing ? 'Retour à la sortie' : 'Sorties'}
      </Link>
      <h1 className={styles.title}>{editing ? 'Modifier la sortie' : 'Nouvelle sortie'}</h1>

      <div className={styles.columns}>
        <form className={styles.form} onSubmit={(event) => void submit(event)} noValidate>
          {formError && <Notice tone="danger">{formError}</Notice>}
          <Input label="Titre" placeholder="Ex. Tour du Glacier Blanc" value={title} maxLength={80} onChange={(e) => setTitle(e.target.value)} error={errors.title} disabled={!loaded} />
          <div className={styles.row}>
            <Input label="Date" type="date" value={date} onChange={(e) => setDate(e.target.value)} error={errors.starts_at} disabled={!loaded} />
            <Input label="Heure" type="time" value={time} onChange={(e) => setTime(e.target.value)} disabled={!loaded} />
            <Input label="Places max" type="number" min={2} max={50} value={places} onChange={(e) => setPlaces(e.target.value)} error={errors.max_participants} disabled={!loaded} />
          </div>

          <div className={styles.field}>
            <span className={styles.label}>Visibilité</span>
            <div className={styles.chips} role="radiogroup" aria-label="Visibilité">
              <Chip role="radio" aria-checked={visibility === 'public'} selected={visibility === 'public'} onClick={() => setVisibility('public')}>
                Publique
              </Chip>
              <Chip role="radio" aria-checked={visibility === 'invitation'} selected={visibility === 'invitation'} onClick={() => setVisibility('invitation')}>
                Sur invitation
              </Chip>
            </div>
            <p className={styles.hint}>
              {visibility === 'public'
                ? 'Visible par tous, et ses refuges apparaissent avec le filtre « Avec sortie ».'
                : 'Visible seulement par les personnes que vous invitez depuis la sortie ou leur profil.'}
            </p>
          </div>

          <div className={styles.field}>
            <span className={styles.label}>Points de stop</span>
            <ol className={styles.stops}>
              {stops.map((stop, index) => (
                <li
                  key={stop.key}
                  className={cx(styles.stop, dragIndex === index && styles.dragging)}
                  draggable
                  onDragStart={(event: DragEvent) => {
                    setDragIndex(index)
                    event.dataTransfer.effectAllowed = 'move'
                  }}
                  onDragOver={(event) => {
                    event.preventDefault()
                    if (dragIndex !== null && dragIndex !== index) {
                      move(dragIndex, index)
                      setDragIndex(index)
                    }
                  }}
                  onDragEnd={() => setDragIndex(null)}
                >
                  <button type="button" className={styles.handle} aria-label={`Déplacer « ${stop.name} » (flèches haut et bas)`} onKeyDown={(event) => onHandleKey(event, index)}>
                    <GripVertical aria-hidden size={16} />
                  </button>
                  <StopNumber value={index + 1} size="sm" />
                  {stop.refuge_id ? (
                    <span className={styles.stopName}>
                      {stop.name}
                      {stop.altitude !== null && <span className={styles.stopMeta}> · {formatAltitude(stop.altitude)}</span>}
                    </span>
                  ) : (
                    <input
                      className={styles.stopInput}
                      aria-label={`Nom du point ${index + 1}`}
                      value={stop.name}
                      maxLength={200}
                      onChange={(e) => setStops((current) => current.map((s) => (s.key === stop.key ? { ...s, name: e.target.value } : s)))}
                    />
                  )}
                  <button type="button" className={styles.remove} aria-label={`Retirer « ${stop.name} »`} onClick={() => setStops((current) => current.filter((s) => s.key !== stop.key))}>
                    <X aria-hidden size={14} />
                  </button>
                </li>
              ))}
            </ol>
            {errors.stops && <p className={styles.error}>{errors.stops}</p>}
            {adding ? (
              <AddStopPanel
                onRefuge={(refuge) => {
                  addStop(fromRefuge(refuge))
                  setFitKey(`refuge-${refuge.id}-${stops.length}`)
                }}
                onFreePoint={() => {
                  setMode('free')
                  setAdding(false)
                }}
                onClose={() => setAdding(false)}
              />
            ) : (
              <button type="button" className={styles.addLink} onClick={() => setAdding(true)}>
                <Plus aria-hidden size={14} /> Ajouter un point (refuge ou point libre)
              </button>
            )}
          </div>

          <div className={styles.actions}>
            <Button variant="secondary" fullWidth onClick={() => navigate(backUrl)}>
              Annuler
            </Button>
            <Button type="submit" fullWidth disabled={submitting || !loaded}>
              {submitting ? 'Enregistrement…' : editing ? 'Enregistrer' : 'Créer la sortie'}
            </Button>
          </div>
          {editing && (
            <button type="button" className={styles.delete} onClick={() => void remove()}>
              Supprimer la sortie
            </button>
          )}
        </form>

        <div className={styles.mapBox}>
          <Suspense fallback={null}>
            <OutingMap stops={stops} path={path} onMapClick={mode === 'idle' ? undefined : handleMapClick} fitKey={fitKey} />
          </Suspense>
          <p className={styles.mapHint}>{HINTS[mode]}</p>
          <div className={styles.tools} role="toolbar" aria-label="Outils de tracé">
            <button type="button" className={cx(styles.tool, mode === 'draw' && styles.toolActive)} aria-pressed={mode === 'draw'} title="Tracer le chemin" onClick={() => setMode(mode === 'draw' ? 'idle' : 'draw')}>
              <Pencil aria-hidden size={16} />
            </button>
            <button type="button" className={styles.tool} title="Annuler le dernier point du chemin" disabled={path.length === 0} onClick={() => setPath((current) => current.slice(0, -1))}>
              <Undo2 aria-hidden size={16} />
            </button>
            <button type="button" className={styles.tool} title="Effacer le chemin" disabled={path.length === 0} onClick={() => setPath([])}>
              <Eraser aria-hidden size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/** Recherche d'un refuge, ou point libre à placer sur la carte. */
function AddStopPanel({ onRefuge, onFreePoint, onClose }: { onRefuge: (refuge: RefugeSummary) => void; onFreePoint: () => void; onClose: () => void }) {
  const [search, setSearch] = useState('')
  const [results, setResults] = useState<RefugeSummary[]>([])
  const term = search.trim()

  useEffect(() => {
    if (term.length < 2) return
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      refugesApi
        .list({ q: term, limit: SEARCH_LIMIT }, controller.signal)
        .then((list) => setResults(list.items))
        .catch(() => undefined)
    }, 250)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [term])

  return (
    <div className={styles.addPanel}>
      <Input
        type="search"
        aria-label="Rechercher un refuge"
        placeholder="Rechercher un refuge…"
        icon={<Search aria-hidden size={16} />}
        value={search}
        autoFocus
        onChange={(e) => setSearch(e.target.value)}
      />
      {term.length >= 2 && (
        <ul className={styles.results}>
          {results.map((refuge) => (
            <li key={refuge.id}>
              <button type="button" className={styles.result} onClick={() => onRefuge(refuge)}>
                <span>{refuge.name}</span>
                <span className={styles.stopMeta}>
                  {[refuge.massif?.name, refuge.altitude && formatAltitude(refuge.altitude)].filter(Boolean).join(' · ')}
                </span>
              </button>
            </li>
          ))}
          {results.length === 0 && <li className={styles.stopMeta}>Aucun refuge trouvé.</li>}
        </ul>
      )}
      <div className={styles.panelActions}>
        <Button size="sm" variant="secondary" icon={<MapPin aria-hidden size={14} />} onClick={onFreePoint}>
          Placer un point libre
        </Button>
        <Button size="sm" variant="secondary" onClick={onClose}>
          Fermer
        </Button>
      </div>
    </div>
  )
}
