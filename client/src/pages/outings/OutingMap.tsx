import 'leaflet/dist/leaflet.css'
import { divIcon, latLngBounds, type LatLngExpression } from 'leaflet'
import { useEffect, useMemo, type ReactNode } from 'react'
import { MapContainer, Marker, Polyline, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import type { LatLng } from '../../api/outings'
import { escapeHtml } from '../../lib/format'
import { colors } from '../../styles/tokens'
import { ATTRIBUTION, TILE_URL } from '../map/tiles'
import styles from './OutingMap.module.css'

// Massif des Écrins, quand il n'y a encore rien à montrer.
const DEFAULT_CENTER: LatLng = [44.9, 6.4]
const DEFAULT_ZOOM = 11

export type MapStop = { latitude: number; longitude: number; name: string }

type OutingMapProps = {
  stops: MapStop[]
  path: LatLng[]
  /** Clic sur la carte (écran 12 : tracer le chemin ou placer un point libre). */
  onMapClick?: (point: LatLng) => void
  /** Recadre la carte quand cette valeur change (chargement d'une sortie, ajout d'un refuge). */
  fitKey?: string
  className?: string
  children?: ReactNode
}

function stopIcon(position: number, name: string) {
  return divIcon({
    className: styles.marker,
    html:
      `<span class="${styles.number}">${position}</span>` +
      `<span class="${styles.label}">${escapeHtml(name)}</span>`,
    iconSize: undefined,
    iconAnchor: [16, 16],
  })
}

function ClickHandler({ onClick }: { onClick: (point: LatLng) => void }) {
  useMapEvents({ click: (event) => onClick([event.latlng.lat, event.latlng.lng]) })
  return null
}

/** Cadre la carte sur les points de stop et le chemin. */
function FitBounds({ points, fitKey }: { points: LatLng[]; fitKey?: string }) {
  const map = useMap()
  useEffect(() => {
    if (points.length === 1) map.setView(points[0], 14)
    if (points.length > 1) map.fitBounds(latLngBounds(points), { padding: [48, 48], maxZoom: 15 })
    // Seulement quand `fitKey` change : pas à chaque point tracé.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, fitKey])
  return null
}

/** Carte d'une sortie : chemin en orange et points de stop numérotés (écrans 11 et 12). */
export function OutingMap({ stops, path, onMapClick, fitKey, className, children }: OutingMapProps) {
  const stopPoints = useMemo(() => stops.map((s): LatLng => [s.latitude, s.longitude]), [stops])
  const all = [...stopPoints, ...path]
  return (
    <MapContainer
      center={DEFAULT_CENTER}
      zoom={DEFAULT_ZOOM}
      className={`${styles.map} ${onMapClick ? styles.editable : ''} ${className ?? ''}`}
    >
      <TileLayer url={TILE_URL} attribution={ATTRIBUTION} maxZoom={19} />
      <FitBounds points={all} fitKey={fitKey} />
      {onMapClick && <ClickHandler onClick={onMapClick} />}
      {path.length >= 2 ? (
        <Polyline positions={path as LatLngExpression[]} pathOptions={{ color: colors.accent, weight: 4 }} />
      ) : (
        // Pas de chemin tracé : les points de stop sont reliés en pointillés.
        stopPoints.length >= 2 && (
          <Polyline
            positions={stopPoints as LatLngExpression[]}
            pathOptions={{ color: colors.accent, weight: 3, dashArray: '6 8' }}
          />
        )
      )}
      {stops.map((stop, index) => (
        <Marker
          key={`${index}-${stop.latitude}-${stop.longitude}`}
          position={[stop.latitude, stop.longitude]}
          icon={stopIcon(index + 1, stop.name)}
          interactive={false}
        />
      ))}
      {children}
    </MapContainer>
  )
}
