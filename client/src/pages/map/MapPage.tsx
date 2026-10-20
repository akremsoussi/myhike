import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import type { LatLngBounds, Map as LeafletMap } from 'leaflet'
import { Search } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, useMapEvents } from 'react-leaflet'
import { refugesApi, type RefugeList, type RefugeSummary } from '../../api/refuges'
import { Chip, Input, Notice } from '../../components'
import { ApiError } from '../../lib/api'
import { formatNumber } from '../../lib/format'
import styles from './MapPage.module.css'
import { RefugeListItem } from './RefugeListItem'
import { RefugeMarkers } from './RefugeMarkers'
import { RefugePopup } from './RefugePopup'
import { ATTRIBUTION, TILE_URL } from './tiles'
import { ZoomControl } from './ZoomControl'

// Vue initiale : massif des Écrins, comme la maquette.
const INITIAL_CENTER: [number, number] = [44.9, 6.4]
const INITIAL_ZOOM = 11
const SELECT_ZOOM = 14
// Nombre maximal d'étiquettes chargées pour la zone visible, et de cartes dans la liste.
const MAP_LIMIT = 2000
const LIST_LIMIT = 100
const SEARCH_LIMIT = 50

type Filter = 'all' | 'guarded' | 'unguarded' | 'outing'

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'Tous' },
  { value: 'guarded', label: 'Gardés' },
  { value: 'unguarded', label: 'Non gardés' },
  // Refuges d'une sortie à venir visible.
  { value: 'outing', label: 'Avec sortie' },
]

const GUARDED_BY_FILTER: Record<Filter, boolean | undefined> = {
  all: undefined,
  guarded: true,
  unguarded: false,
  outing: undefined,
}

function toBbox(bounds: LatLngBounds): [number, number, number, number] {
  return [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()]
}

/** Refuges les plus proches du centre de la carte en premier. */
function byDistanceTo(bounds: LatLngBounds | null, refuges: RefugeSummary[]): RefugeSummary[] {
  if (!bounds) return refuges
  const center = bounds.getCenter()
  // Distance approchée : suffisante pour trier, la longitude étant corrigée par la latitude.
  const cos = Math.cos((center.lat * Math.PI) / 180)
  const distance = (r: RefugeSummary) => (r.latitude - center.lat) ** 2 + ((r.longitude - center.lng) * cos) ** 2
  return [...refuges].sort((a, b) => distance(a) - distance(b))
}

/** Transmet la zone visible après chaque déplacement de la carte. */
function BoundsWatcher({ onChange }: { onChange: (bounds: LatLngBounds) => void }) {
  const map = useMapEvents({ moveend: () => onChange(map.getBounds()) })
  useEffect(() => onChange(map.getBounds()), [map, onChange])
  return null
}

/** Charge des refuges dès que `query` change, en annulant la requête précédente. */
function useRefuges(query: Parameters<typeof refugesApi.list>[0] | null, delayMs: number) {
  const [data, setData] = useState<RefugeList | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const key = query ? JSON.stringify(query) : null

  useEffect(() => {
    if (!key) return
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      setLoading(true)
      refugesApi
        .list(JSON.parse(key), controller.signal)
        .then((result) => {
          setData(result)
          setError(null)
        })
        .catch((err: unknown) => {
          if (controller.signal.aborted) return
          setError(err instanceof ApiError ? err.message : 'Les refuges n’ont pas pu être chargés.')
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false)
        })
    }, delayMs)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [key, delayMs])

  return { data, loading, error }
}

/** Écran 03 · Carte des refuges. */
export function MapPage() {
  const [map, setMap] = useState<LeafletMap | null>(null)
  const [bounds, setBounds] = useState<LatLngBounds | null>(null)
  const [filter, setFilter] = useState<Filter>('all')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<RefugeSummary | null>(null)
  const itemRefs = useRef(new Map<number, HTMLButtonElement>())

  const guarded = GUARDED_BY_FILTER[filter]
  const withOuting = filter === 'outing' || undefined
  const term = search.trim()
  const searching = term.length >= 2

  const zone = useRefuges(bounds ? { bbox: toBbox(bounds), guarded, withOuting, limit: MAP_LIMIT } : null, 250)
  const results = useRefuges(searching ? { q: term, guarded, withOuting, limit: SEARCH_LIMIT } : null, 300)

  const zoneItems = zone.data?.items ?? []
  const listItems = searching
    ? (results.data?.items ?? [])
    : byDistanceTo(bounds, zoneItems).slice(0, LIST_LIMIT)
  const total = searching ? (results.data?.total ?? 0) : (zone.data?.total ?? 0)
  const loading = searching ? results.loading : zone.loading
  const error = searching ? results.error : zone.error

  function select(refuge: RefugeSummary, fly: boolean) {
    setSelected(refuge)
    if (fly && map) {
      map.flyTo([refuge.latitude, refuge.longitude], Math.max(map.getZoom(), SELECT_ZOOM), { duration: 0.8 })
    }
  }

  // Refuge choisi sur la carte : on fait défiler la liste jusqu'à lui.
  useEffect(() => {
    if (selected) itemRefs.current.get(selected.id)?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [selected])

  let countLabel: string
  if (searching) {
    countLabel = `${formatNumber(total)} résultat${total > 1 ? 's' : ''}`
  } else {
    countLabel = `${formatNumber(total)} refuge${total > 1 ? 's' : ''} dans cette zone`
  }

  return (
    <div className={styles.page}>
      <aside className={styles.panel}>
        <div className={styles.panelHeader}>
          <h1 className={styles.title}>Refuges</h1>
          <p className={styles.count} aria-live="polite">
            {loading && !zone.data ? 'Chargement…' : countLabel}
          </p>
          <Input
            type="search"
            aria-label="Rechercher un refuge"
            placeholder="Refuge, massif…"
            icon={<Search aria-hidden size={16} />}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <div className={styles.filters} role="group" aria-label="Filtrer les refuges">
            {FILTERS.map((item) => (
              <Chip
                key={item.value}
                selected={filter === item.value}
                onClick={() => setFilter(item.value)}
              >
                {item.label}
              </Chip>
            ))}
          </div>
        </div>

        <div className={styles.list}>
          {error && <Notice tone="danger">{error}</Notice>}
          {!searching && total > zoneItems.length && (
            <Notice>Zoomez pour afficher tous les refuges de la zone sur la carte.</Notice>
          )}
          {listItems.map((refuge) => (
            <RefugeListItem
              key={refuge.id}
              refuge={refuge}
              selected={selected?.id === refuge.id}
              onSelect={(item) => select(item, true)}
              ref={(element) => {
                if (element) itemRefs.current.set(refuge.id, element)
                else itemRefs.current.delete(refuge.id)
              }}
            />
          ))}
          {!loading && listItems.length === 0 && !error && (
            <p className={styles.empty}>
              {searching ? 'Aucun refuge ne correspond à cette recherche.' : 'Aucun refuge dans cette zone.'}
            </p>
          )}
          {!searching && total > listItems.length && listItems.length > 0 && (
            <p className={styles.empty}>
              … et {formatNumber(total - listItems.length)} autres. Zoomez ou cherchez un nom.
            </p>
          )}
        </div>
      </aside>

      <div className={styles.mapArea}>
        <MapContainer
          ref={setMap}
          center={INITIAL_CENTER}
          zoom={INITIAL_ZOOM}
          zoomControl={false}
          className={styles.map}
        >
          <TileLayer url={TILE_URL} attribution={ATTRIBUTION} maxZoom={19} />
          <BoundsWatcher onChange={setBounds} />
          <RefugeMarkers refuges={zoneItems} selectedId={selected?.id ?? null} onSelect={(r) => select(r, false)} />
          {selected && <RefugePopup refuge={selected} onClose={() => setSelected(null)} />}
          <ZoomControl />
        </MapContainer>
      </div>
    </div>
  )
}
