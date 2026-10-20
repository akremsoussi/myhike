import L from 'leaflet'
import 'leaflet.markercluster'
import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import type { RefugeSummary } from '../../api/refuges'
import { cx } from '../../lib/cx'
import { escapeHtml, formatNumber } from '../../lib/format'
import styles from './MapPage.module.css'

type RefugeMarkersProps = {
  refuges: RefugeSummary[]
  selectedId: number | null
  onSelect: (refuge: RefugeSummary) => void
}

// Étiquette « • Nom du refuge » ; ancrée en son centre (conteneur de taille nulle).
function pinIcon(refuge: RefugeSummary, selected: boolean): L.DivIcon {
  return L.divIcon({
    className: styles.pinAnchor,
    iconSize: [0, 0],
    html: `<span class="${cx(styles.pin, selected && styles.pinSelected)}"><span class="${styles.pinDot}"></span>${escapeHtml(refuge.name)}</span>`,
  })
}

function clusterIcon(cluster: L.MarkerCluster): L.DivIcon {
  return L.divIcon({
    className: styles.pinAnchor,
    iconSize: [0, 0],
    html: `<span class="${styles.cluster}">${formatNumber(cluster.getChildCount())}</span>`,
  })
}

/**
 * Étiquettes des refuges, regroupées quand elles se chevauchent.
 * Gérées directement avec Leaflet : plusieurs milliers de marqueurs React seraient trop lents.
 */
export function RefugeMarkers({ refuges, selectedId, onSelect }: RefugeMarkersProps) {
  const map = useMap()
  const clusterRef = useRef<L.MarkerClusterGroup | null>(null)
  const markersRef = useRef(new Map<number, { marker: L.Marker; refuge: RefugeSummary }>())
  const selectedRef = useRef(selectedId)
  const onSelectRef = useRef(onSelect)

  useEffect(() => {
    onSelectRef.current = onSelect
  }, [onSelect])

  useEffect(() => {
    const cluster = L.markerClusterGroup({
      iconCreateFunction: clusterIcon,
      showCoverageOnHover: false,
      maxClusterRadius: 90,
      disableClusteringAtZoom: 15,
      spiderfyOnMaxZoom: false,
    })
    map.addLayer(cluster)
    clusterRef.current = cluster
    return () => {
      map.removeLayer(cluster)
      clusterRef.current = null
    }
  }, [map])

  // Nouvelle liste : on remplace toutes les étiquettes.
  useEffect(() => {
    const cluster = clusterRef.current
    if (!cluster) return
    const markers = markersRef.current
    cluster.clearLayers()
    markers.clear()
    const layers = refuges.map((refuge) => {
      const marker = L.marker([refuge.latitude, refuge.longitude], {
        icon: pinIcon(refuge, refuge.id === selectedRef.current),
        title: refuge.name,
        riseOnHover: true,
        keyboard: true,
      })
      marker.on('click', () => onSelectRef.current(refuge))
      markers.set(refuge.id, { marker, refuge })
      return marker
    })
    cluster.addLayers(layers)
  }, [refuges])

  // Changement de sélection : seules deux étiquettes changent d'apparence.
  useEffect(() => {
    const markers = markersRef.current
    const previous = selectedRef.current
    selectedRef.current = selectedId
    if (previous !== null) {
      const entry = markers.get(previous)
      entry?.marker.setIcon(pinIcon(entry.refuge, false))
    }
    if (selectedId !== null) {
      const entry = markers.get(selectedId)
      if (entry) {
        entry.marker.setIcon(pinIcon(entry.refuge, true))
        entry.marker.setZIndexOffset(1000)
      }
    }
  }, [selectedId])

  return null
}
