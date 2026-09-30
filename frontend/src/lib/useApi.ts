import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from 'react'
import { ApiError } from './api'

type ApiState<T> = {
  data: T | null
  /** Message affichable, null si tout va bien. */
  error: string | null
  /** Code de l'erreur (« not_found »…), pour afficher un écran adapté. */
  errorCode: string | null
  loading: boolean
  /** Mise à jour locale après une action (rejoindre, j'aime…), sans recharger. */
  setData: Dispatch<SetStateAction<T | null>>
  reload: () => void
}

/** Charge `load()` au montage et chaque fois que `key` change. */
export function useApi<T>(key: string, load: () => Promise<T>, fallbackError: string): ApiState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<{ message: string; code: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    load()
      .then((result) => {
        if (cancelled) return
        setData(result)
        setError(null)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setError(
          err instanceof ApiError ? { message: err.message, code: err.code } : { message: fallbackError, code: 'unknown' },
        )
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
    // `load` change à chaque rendu : c'est `key` qui décide quand recharger.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, version])

  const reload = useCallback(() => setVersion((value) => value + 1), [])

  return { data, error: error?.message ?? null, errorCode: error?.code ?? null, loading, setData, reload }
}
