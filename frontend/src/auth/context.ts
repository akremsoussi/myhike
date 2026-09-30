import { createContext, useContext } from 'react'
import type { Me } from '../api/auth'

export type AuthContextValue = {
  /** undefined : session en cours de vérification ; null : visiteur non connecté. */
  me: Me | null | undefined
  setMe: (me: Me | null) => void
  refresh: () => Promise<Me | null>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (value === null) {
    throw new Error('useAuth doit être utilisé dans <AuthProvider>.')
  }
  return value
}
