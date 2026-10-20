import type { Visibility } from '../components'
import { api } from '../lib/api'
import type { Photo } from './media'
import type { Massif, RefugeSummary } from './refuges'

/** Ce qu'on montre d'un utilisateur à côté de son contenu. */
export type Author = { id: number; username: string; display_name: string }

export type Community = {
  id: number
  slug: string
  name: string
  description: string
  /** Alpes, Pyrénées, Préalpes… */
  region: string
  massif: Massif | null
  member_count: number
  post_count: number
  is_member: boolean
  banner: Photo | null
  icon: Photo | null
}

export type CommunityDetail = Community & {
  /** Quelques membres récents (colonne latérale de l'écran 08). */
  members: Author[]
  refuges: RefugeSummary[]
}

/** [latitude, longitude], ou [latitude, longitude, altitude] pour un chemin importé (GPX). */
export type PathPoint = [number, number] | [number, number, number]

export type Post = {
  id: number
  author: Author
  community: { slug: string; name: string } | null
  /** Refuge dont parle le post (« Voir les posts liés » de la fiche refuge). */
  refuge: { id: number; name: string } | null
  /** Vide si le post n'a que des photos ou un chemin. */
  body: string
  photos: Photo[]
  /** Chemin simplifié pour l'aperçu, null sans chemin. */
  path: [number, number][] | null
  distance_m: number | null
  /** Calculé à partir des altitudes d'un GPX ; null pour un chemin tracé sur la carte. */
  elevation_gain_m: number | null
  visibility: Visibility
  created_at: string
  like_count: number
  liked: boolean
  can_delete: boolean
}

export type PostPage = { items: Post[]; next_before: number | null }

export type NewPost = {
  body: string
  visibility: Visibility
  community_slug?: string
  /** Images envoyées avant avec `mediaApi.upload`, dans l'ordre d'affichage. */
  photo_ids?: number[]
  path?: PathPoint[]
  refuge_id?: number
}

export type Member = { user: Author; joined_at: string }

/** Liste complète des membres : `total` correspond à la recherche. */
export type MemberPage = { total: number; items: Member[] }

export type Likes = { like_count: number; liked: boolean }

export const communitiesApi = {
  list: () => api<Community[]>('/communities'),
  get: (slug: string) => api<CommunityDetail>(`/communities/${encodeURIComponent(slug)}`),
  join: (slug: string) =>
    api<Community>(`/communities/${encodeURIComponent(slug)}/membership`, { method: 'PUT' }),
  leave: (slug: string) =>
    api<Community>(`/communities/${encodeURIComponent(slug)}/membership`, { method: 'DELETE' }),
  posts: (slug: string, before?: number) =>
    api<PostPage>(
      `/communities/${encodeURIComponent(slug)}/posts${before ? `?before=${before}` : ''}`,
    ),
  members: (slug: string, query: { q?: string; offset?: number; limit?: number }, signal?: AbortSignal) => {
    const params = new URLSearchParams()
    if (query.q) params.set('q', query.q)
    if (query.offset) params.set('offset', String(query.offset))
    if (query.limit) params.set('limit', String(query.limit))
    return api<MemberPage>(`/communities/${encodeURIComponent(slug)}/members?${params.toString()}`, { signal })
  },
}

export const postsApi = {
  create: (post: NewPost) => api<Post>('/posts', { method: 'POST', body: post }),
  remove: (id: number) => api<void>(`/posts/${id}`, { method: 'DELETE' }),
  like: (id: number) => api<Likes>(`/posts/${id}/like`, { method: 'PUT' }),
  unlike: (id: number) => api<Likes>(`/posts/${id}/like`, { method: 'DELETE' }),
}
