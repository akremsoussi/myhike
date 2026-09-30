import type { Visibility } from '../components'
import { api } from '../lib/api'
import type { Author, PostPage } from './communities'
import type { OutingSummary } from './outings'

export type Relation = 'self' | 'none' | 'friends' | 'request_sent' | 'request_received'

export type CommunityRef = { slug: string; name: string }

/** Écrans 05 (soi-même) et 06 / 06b (quelqu'un d'autre). */
export type Profile = {
  user: Author
  member_since: string
  relation: Relation
  /** Date où l'amitié a été acceptée (« Ami depuis mars 2026 »). */
  friends_since: string | null
  post_count: number
  community_count: number
  /** Sorties où la personne a participé ; null si masquées par ses paramètres. */
  outing_count: number | null
  /** null si le réglage « Qui peut voir ma liste d'amis » ne l'autorise pas. */
  friend_count: number | null
  /** Soi-même : ses communautés. Quelqu'un d'autre : les communautés en commun. */
  communities: CommunityRef[]
  /** Posts « Amis uniquement » cachés au visiteur. */
  hidden_post_count: number
  can_send_request: boolean
  /** Soi-même seulement. */
  pending_request_count: number | null
  friends_preview: Author[] | null
}

export type Friend = { user: Author; since: string | null }

export type FriendRequest = { user: Author; created_at: string; common_community_count: number }

export type Friends = { friends: Friend[]; received: FriendRequest[]; sent: FriendRequest[] }

export type Suggestion = { user: Author; community: CommunityRef; mutual_friend_count: number }

export type Audience = 'everyone' | 'friends' | 'me'

export type RequestPolicy = 'everyone' | 'communities'

/** Écran 05c. */
export type PrivacySettings = {
  default_post_visibility: Visibility
  friends_list_audience: Audience
  outings_audience: Audience
  friend_requests_from: RequestPolicy
  show_in_suggestions: boolean
}

type RelationResult = { relation: Relation }

const user = (username: string) => encodeURIComponent(username)

export const usersApi = {
  profile: (username: string) => api<Profile>(`/users/${user(username)}`),
  posts: (username: string, before?: number) =>
    api<PostPage>(`/users/${user(username)}/posts${before ? `?before=${before}` : ''}`),
  /** Sorties à venir ; `hidden` : masquées par le réglage « Qui peut voir mes sorties à venir ». */
  outings: (username: string) =>
    api<{ items: OutingSummary[]; hidden: boolean }>(`/users/${user(username)}/outings`),
  privacy: () => api<PrivacySettings>('/me/privacy'),
  updatePrivacy: (settings: PrivacySettings) =>
    api<PrivacySettings>('/me/privacy', { method: 'PUT', body: settings }),
}

export const friendsApi = {
  list: () => api<Friends>('/friends'),
  suggestions: () => api<Suggestion[]>('/friends/suggestions'),
  /** « + Ajouter en ami » (accepte directement si l'autre nous avait demandé). */
  request: (username: string) => api<RelationResult>(`/friends/${user(username)}`, { method: 'POST' }),
  accept: (username: string) => api<RelationResult>(`/friends/${user(username)}/accept`, { method: 'POST' }),
  decline: (username: string) => api<RelationResult>(`/friends/${user(username)}/decline`, { method: 'POST' }),
  cancel: (username: string) => api<RelationResult>(`/friends/${user(username)}/request`, { method: 'DELETE' }),
  remove: (username: string) => api<RelationResult>(`/friends/${user(username)}`, { method: 'DELETE' }),
}
