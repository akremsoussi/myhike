/** Mêmes calculs que l'API (backend/app/services/geo.py), pour afficher les chiffres avant de publier. */

const EARTH_RADIUS_M = 6_371_000
/** Variation d'altitude ignorée : le bruit des altitudes GPS gonflerait le dénivelé. */
const ELEVATION_THRESHOLD_M = 5

type Point = readonly number[]

function haversineM(a: Point, b: Point): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180
  const [lat1, lng1, lat2, lng2] = [a[0], a[1], b[0], b[1]].map(toRad)
  const h = Math.sin((lat2 - lat1) / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin((lng2 - lng1) / 2) ** 2
  return 2 * EARTH_RADIUS_M * Math.asin(Math.sqrt(h))
}

/** Longueur d'un chemin [latitude, longitude, …], en mètres. */
export function pathLengthM(points: readonly Point[]): number {
  let total = 0
  for (let i = 1; i < points.length; i++) total += haversineM(points[i - 1], points[i])
  return Math.round(total)
}

/** Dénivelé positif, ou null si un point n'a pas d'altitude (chemin tracé à la main). */
export function elevationGainM(points: readonly Point[]): number | null {
  if (points.length === 0 || points.some((point) => point.length < 3)) return null
  let gain = 0
  let reference = points[0][2]
  for (const point of points.slice(1)) {
    const altitude = point[2]
    if (altitude - reference >= ELEVATION_THRESHOLD_M) {
      gain += altitude - reference
      reference = altitude
    } else if (reference - altitude >= ELEVATION_THRESHOLD_M) {
      reference = altitude
    }
  }
  return Math.round(gain)
}

/** Garde au plus `max` points, régulièrement espacés, avec le premier et le dernier. */
export function downsample<T>(points: T[], max: number): T[] {
  if (points.length <= max) return points
  const step = (points.length - 1) / (max - 1)
  return Array.from({ length: max }, (_, i) => points[Math.round(i * step)])
}
