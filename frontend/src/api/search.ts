import { api } from '../lib/api'
import type { Author, Community, Post } from './communities'
import type { OutingSummary } from './outings'
import type { RefugeSummary } from './refuges'

/** Recherche globale (barre de navigation) : les premiers résultats de chaque catégorie. */
export type SearchResults = {
  refuges: RefugeSummary[]
  communities: Community[]
  users: Author[]
  outings: OutingSummary[]
  posts: Post[]
}

/** Longueur minimale acceptée par l'API. */
export const SEARCH_MIN_LENGTH = 2

export const searchApi = {
  search: (q: string) => api<SearchResults>(`/search?q=${encodeURIComponent(q)}`),
}
