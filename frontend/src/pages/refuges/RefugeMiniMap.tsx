import 'leaflet/dist/leaflet.css'
import { CircleMarker, MapContainer, TileLayer } from 'react-leaflet'
import { colors } from '../../styles/tokens'
import { ATTRIBUTION, TILE_URL } from '../map/tiles'
import styles from './RefugePage.module.css'

const ZOOM = 13

type RefugeMiniMapProps = { latitude: number; longitude: number; name: string }

/** Petite carte centrée sur le refuge (bloc « Accès »). Chargée à la demande avec Leaflet. */
export function RefugeMiniMap({ latitude, longitude, name }: RefugeMiniMapProps) {
  return (
    <MapContainer
      center={[latitude, longitude]}
      zoom={ZOOM}
      scrollWheelZoom={false}
      className={styles.miniMap}
      aria-label={`Carte : ${name}`}
    >
      <TileLayer url={TILE_URL} attribution={ATTRIBUTION} maxZoom={19} />
      <CircleMarker
        center={[latitude, longitude]}
        radius={8}
        pathOptions={{ color: colors.onPrimary, weight: 3, fillColor: colors.primary, fillOpacity: 1 }}
      />
    </MapContainer>
  )
}
