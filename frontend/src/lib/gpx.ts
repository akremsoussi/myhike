import type { PathPoint } from '../api/communities'

/** Lit le premier tracé d'un fichier GPX : points de trace, sinon de route. Altitude gardée si présente. */
export function parseGpx(text: string): PathPoint[] {
  const doc = new DOMParser().parseFromString(text, 'application/xml')
  if (doc.querySelector('parsererror')) throw new Error('Ce fichier n’est pas un GPX valide.')
  let nodes = Array.from(doc.getElementsByTagName('trkpt'))
  if (nodes.length < 2) nodes = Array.from(doc.getElementsByTagName('rtept'))
  const points: PathPoint[] = []
  for (const node of nodes) {
    const lat = Number(node.getAttribute('lat'))
    const lng = Number(node.getAttribute('lon'))
    if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) continue
    const ele = node.getElementsByTagName('ele')[0]?.textContent
    const altitude = ele ? Number(ele) : NaN
    points.push(Number.isFinite(altitude) ? [lat, lng, Math.round(altitude * 10) / 10] : [lat, lng])
  }
  if (points.length < 2) throw new Error('Aucun tracé trouvé dans ce fichier GPX.')
  // Altitudes partielles : on les retire toutes, le dénivelé serait faux.
  if (points.some((point) => point.length === 2)) return points.map(([lat, lng]) => [lat, lng])
  return points
}
