import { api } from '../lib/api'

export type RefugeKind = 'unguarded_hut' | 'gite' | 'guarded_hut'

export type Massif = { id: number; name: string }

export type RefugeSummary = {
  id: number
  name: string
  kind: RefugeKind
  is_guarded: boolean
  latitude: number
  longitude: number
  altitude: number | null
  capacity: number | null
  /** État brut de refuges.info (« Fermée »…), null si ouvert. */
  state: string | null
  massif: Massif | null
}

/** Fiche refuge (écran 04). Textes issus de refuges.info (CC BY-SA 2.0). */
export type RefugeDetail = RefugeSummary & {
  access: string | null
  remarks: string | null
  owner_info: string | null
  /** Premier numéro trouvé dans `owner_info`, « 04 92 23 50 24 ». */
  phone: string | null
  source_url: string | null
  source_updated_at: string | null
}

export type RefugeList = { total: number; items: RefugeSummary[] }

export type RefugeQuery = {
  /** [ouest, sud, est, nord] */
  bbox?: [number, number, number, number]
  guarded?: boolean
  /** Seulement les refuges d'une sortie à venir (filtre « Avec sortie »). */
  withOuting?: boolean
  q?: string
  limit?: number
}

function toSearchParams(query: RefugeQuery): string {
  const params = new URLSearchParams()
  if (query.bbox) params.set('bbox', query.bbox.map((value) => value.toFixed(5)).join(','))
  if (query.guarded !== undefined) params.set('guarded', String(query.guarded))
  if (query.withOuting) params.set('with_outing', 'true')
  if (query.q) params.set('q', query.q)
  if (query.limit) params.set('limit', String(query.limit))
  return params.toString()
}

export const refugesApi = {
  list: (query: RefugeQuery, signal?: AbortSignal) =>
    api<RefugeList>(`/refuges?${toSearchParams(query)}`, { signal }),
  get: (id: number) => api<RefugeDetail>(`/refuges/${id}`),
}
