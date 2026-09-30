import type { Visibility } from '../components'
import { api } from '../lib/api'
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
}

export type CommunityDetail = Community & {
  /** Quelques membres récents (colonne latérale de l'écran 08). */
  members: Author[]
  refuges: RefugeSummary[]
}

export type Post = {
  id: number
  author: Author
  community: { slug: string; name: string } | null
  body: string
  visibility: Visibility
  created_at: string
  like_count: number
  liked: boolean
  can_delete: boolean
}

export type PostPage = { items: Post[]; next_before: number | null }

export type NewPost = { body: string; visibility: Visibility; community_slug?: string }

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
}

export const postsApi = {
  create: (post: NewPost) => api<Post>('/posts', { method: 'POST', body: post }),
  remove: (id: number) => api<void>(`/posts/${id}`, { method: 'DELETE' }),
  like: (id: number) => api<Likes>(`/posts/${id}/like`, { method: 'PUT' }),
  unlike: (id: number) => api<Likes>(`/posts/${id}/like`, { method: 'DELETE' }),
}
