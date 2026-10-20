import { api } from '../lib/api'

export type AccountStatus = 'pending_email' | 'active' | 'suspended'
export type Role = 'user' | 'moderator' | 'super_admin'

export type User = {
  id: number
  username: string
  display_name: string
  email: string
  role: Role
  status: AccountStatus
  created_at: string
}

/** Lien de confirmation en cours (écran 02b). */
export type Verification = {
  email: string
  sent_at: string
  expires_at: string
  resend_available_at: string
}

export type Me = {
  user: User
  verification: Verification | null
}

export type RegisterInput = {
  username: string
  email: string
  password: string
  accept_terms: boolean
}

export const authApi = {
  me: () => api<Me>('/auth/me'),
  register: (input: RegisterInput) => api<Me>('/auth/register', { method: 'POST', body: input }),
  login: (email: string, password: string) =>
    api<Me>('/auth/login', { method: 'POST', body: { email, password } }),
  logout: () => api<void>('/auth/logout', { method: 'POST' }),
  verifyEmail: (token: string) =>
    api<{ status: AccountStatus }>('/auth/verify-email', { method: 'POST', body: { token } }),
  resendVerification: () => api<Me>('/auth/resend-verification', { method: 'POST' }),
  changePendingEmail: (email: string) => api<Me>('/auth/pending-email', { method: 'PATCH', body: { email } }),
  /** « Mot de passe oublié » : même réponse que l'adresse ait un compte ou non. */
  requestPasswordReset: (email: string) => api<void>('/auth/password-reset', { method: 'POST', body: { email } }),
  /** Ferme toutes les sessions, y compris celle de ce navigateur. */
  resetPassword: (token: string, password: string) =>
    api<void>('/auth/password-reset/confirm', { method: 'POST', body: { token, password } }),
}
