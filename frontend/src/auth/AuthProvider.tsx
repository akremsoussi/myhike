import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authApi, type Me } from '../api/auth'
import { ApiError } from '../lib/api'
import { AuthContext } from './context'

async function fetchMe(): Promise<Me | null> {
  try {
    return await authApi.me()
  } catch (error) {
    // 401 : pas de session ; 403 : compte suspendu. Dans les deux cas, on est déconnecté.
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return null
    }
    throw error
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null | undefined>(undefined)

  const refresh = useCallback(async () => {
    const current = await fetchMe()
    setMe(current)
    return current
  }, [])

  const logout = useCallback(async () => {
    await authApi.logout()
    setMe(null)
  }, [])

  useEffect(() => {
    fetchMe()
      .then(setMe)
      .catch(() => setMe(null))
  }, [])

  const value = useMemo(() => ({ me, setMe, refresh, logout }), [me, refresh, logout])
  return <AuthContext value={value}>{children}</AuthContext>
}
