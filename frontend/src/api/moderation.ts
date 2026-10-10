import type { Visibility } from '../components'
import { api } from '../lib/api'
import type { Author } from './communities'
import type { Photo, UploadedImage } from './media'
import type { Massif, RefugeSummary } from './refuges'
import type { CommunityRef } from './users'

export type ReportReason = 'insulting' | 'spam' | 'fake_profile' | 'other'

export const REPORT_REASONS: Record<ReportReason, string> = {
  insulting: 'Propos insultants',
  spam: 'Spam',
  fake_profile: 'Faux profil',
  other: 'Autre',
}

export type Report = {
  id: number
  reporter: Author
  target: Author
  /** Post signalé, visible par les modérateurs même s'il est « Amis uniquement ». */
  post: { id: number; body: string; photos: Photo[]; visibility: Visibility; community: CommunityRef | null } | null
  reason: ReportReason
  comment: string
  created_at: string
  resolved_at: string | null
}

export type ReportedAccount = {
  user: Author
  report_count: number
  last_reason: ReportReason
  last_community: CommunityRef | null
}

export type Stat = { value: number; recent: number }

export type Dashboard = {
  users: Stat
  communities: Stat
  active_outings: Stat
  reported_accounts: number
  activity: { message: string; actor: Author | null; created_at: string }[]
  reported: ReportedAccount[]
}

export type ModCommunity = {
  slug: string
  name: string
  region: string
  massif: Massif | null
  member_count: number
  post_count: number
  created_at: string
}

export type ModCommunityDetail = ModCommunity & {
  description: string
  refuges: RefugeSummary[]
  banner: UploadedImage | null
  icon: UploadedImage | null
}

export type CommunityInput = {
  name: string
  description: string
  region: string
  massif_id: number | null
  refuge_ids: number[]
  /** Images envoyées avec le type banner / icon ; null : pas de visuel. */
  banner_id: number | null
  icon_id: number | null
}

export type Role = 'user' | 'moderator'
export type AccountStatus = 'pending_email' | 'active' | 'suspended'
export type AccountFilter = 'all' | 'moderators' | 'reported' | 'suspended'

export type Account = {
  id: number
  username: string
  display_name: string
  email: string
  role: Role
  status: AccountStatus
  created_at: string
  open_report_count: number
}

export type AccountDetail = Account & {
  community_count: number
  post_count: number
  outing_count: number
  reports: Report[]
}

const user = (username: string) => encodeURIComponent(username)
const community = (slug: string) => encodeURIComponent(slug)

/** Signaler un post ou un compte (tous les utilisateurs). */
export const reportsApi = {
  create: (report: { post_id?: number; username?: string; reason: ReportReason; comment?: string }) =>
    api<void>('/reports', { method: 'POST', body: report }),
}

/** Réservé aux modérateurs (écrans 13 à 16). */
export const moderationApi = {
  summary: () => api<{ open_reports: number }>('/moderation/summary'),
  dashboard: () => api<Dashboard>('/moderation/dashboard'),
  reports: () => api<Report[]>('/moderation/reports'),
  resolveReport: (id: number) => api<void>(`/moderation/reports/${id}/resolve`, { method: 'POST' }),
  deletePost: (id: number) => api<void>(`/moderation/posts/${id}`, { method: 'DELETE' }),

  communities: () => api<ModCommunity[]>('/moderation/communities'),
  community: (slug: string) => api<ModCommunityDetail>(`/moderation/communities/${community(slug)}`),
  createCommunity: (data: CommunityInput) =>
    api<ModCommunityDetail>('/moderation/communities', { method: 'POST', body: data }),
  updateCommunity: (slug: string, data: CommunityInput) =>
    api<ModCommunityDetail>(`/moderation/communities/${community(slug)}`, { method: 'PUT', body: data }),
  deleteCommunity: (slug: string) => api<void>(`/moderation/communities/${community(slug)}`, { method: 'DELETE' }),

  accounts: (q: string, filter: AccountFilter) =>
    api<{ total: number; moderator_count: number; items: Account[] }>(
      `/moderation/users?${new URLSearchParams({ q, filter })}`,
    ),
  account: (username: string) => api<AccountDetail>(`/moderation/users/${user(username)}`),
  setRole: (username: string, role: Role) =>
    api<AccountDetail>(`/moderation/users/${user(username)}/role`, { method: 'PUT', body: { role } }),
  suspend: (username: string) => api<AccountDetail>(`/moderation/users/${user(username)}/suspend`, { method: 'POST' }),
  reactivate: (username: string) =>
    api<AccountDetail>(`/moderation/users/${user(username)}/reactivate`, { method: 'POST' }),
  resolveAccountReports: (username: string) =>
    api<AccountDetail>(`/moderation/users/${user(username)}/reports/resolve`, { method: 'POST' }),
  deleteAccount: (username: string) => api<void>(`/moderation/users/${user(username)}`, { method: 'DELETE' }),
  /** Téléchargement direct (même origine : le cookie de session suit). */
  exportUrl: '/api/moderation/users/export',
}
