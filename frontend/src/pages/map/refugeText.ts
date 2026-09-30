import type { RefugeSummary } from '../../api/refuges'
import { formatAltitude, formatNumber } from '../../lib/format'

export function isClosed(refuge: RefugeSummary): boolean {
  return refuge.state?.toLowerCase().startsWith('ferm') ?? false
}

/** « Gardé », « Non gardé » ou « Fermé ». */
export function guardLabel(refuge: RefugeSummary): string {
  if (isClosed(refuge)) return 'Fermé'
  return refuge.is_guarded ? 'Gardé' : 'Non gardé'
}

/** « 2 542 m · 60 places », en omettant ce qui est inconnu. */
export function altitudeAndCapacity(refuge: RefugeSummary): string[] {
  const parts: string[] = []
  if (refuge.altitude) parts.push(formatAltitude(refuge.altitude))
  if (refuge.capacity) parts.push(`${formatNumber(refuge.capacity)} places`)
  return parts
}
