import { api } from '../lib/api'
import type { Author } from './communities'

export type LatLng = [number, number]

export type OutingVisibility = 'public' | 'invitation'

export type OutingStatus = 'open' | 'full'

/** Carte de l'écran 10. */
export type OutingSummary = {
  id: number
  title: string
  starts_at: string
  organizer: Author
  visibility: OutingVisibility
  status: OutingStatus
  participant_count: number
  max_participants: number
  stop_count: number
  participants_preview: Author[]
  /** Tracé de la vignette : le chemin, ou à défaut les points de stop. */
  preview: LatLng[]
  is_participant: boolean
}

export type Stop = {
  position: number
  name: string
  latitude: number
  longitude: number
  refuge_id: number | null
  /** Altitude du refuge ; inconnue pour un point libre. */
  altitude: number | null
}

/** Écran 11. */
export type OutingDetail = OutingSummary & {
  stops: Stop[]
  participants: Author[]
  path: LatLng[]
  distance_m: number
  /** Montées entre points de stop d'altitude connue : approximation. */
  elevation_gain_m: number | null
  is_organizer: boolean
  is_invited: boolean
  can_join: boolean
}

/** Un refuge, ou un point libre placé sur la carte. */
export type StopInput = { refuge_id: number } | { name: string; latitude: number; longitude: number }

/** Écran 12. */
export type OutingInput = {
  title: string
  /** ISO avec fuseau. */
  starts_at: string
  max_participants: number
  visibility: OutingVisibility
  stops: StopInput[]
  path: LatLng[]
}

export type OutingScope = 'upcoming' | 'mine' | 'joined' | 'past'

export const outingsApi = {
  list: (scope: OutingScope = 'upcoming', refugeId?: number) =>
    api<OutingSummary[]>(`/outings?scope=${scope}${refugeId ? `&refuge_id=${refugeId}` : ''}`),
  get: (id: number) => api<OutingDetail>(`/outings/${id}`),
  create: (outing: OutingInput) => api<OutingDetail>('/outings', { method: 'POST', body: outing }),
  update: (id: number, outing: OutingInput) =>
    api<OutingDetail>(`/outings/${id}`, { method: 'PUT', body: outing }),
  remove: (id: number) => api<void>(`/outings/${id}`, { method: 'DELETE' }),
  join: (id: number) => api<OutingDetail>(`/outings/${id}/participation`, { method: 'PUT' }),
  leave: (id: number) => api<OutingDetail>(`/outings/${id}/participation`, { method: 'DELETE' }),
  invite: (id: number, username: string) =>
    api<void>(`/outings/${id}/invitations`, { method: 'POST', body: { username } }),
}
