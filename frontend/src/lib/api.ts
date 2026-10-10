/** Appels à l'API FastAPI (même origine grâce au proxy Vite : le cookie de session suit). */

type ErrorDetail = {
  code: string
  message: string
  fields?: Record<string, string>
  retry_after?: number
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly fields: Record<string, string>
  readonly retryAfter?: number

  constructor(status: number, detail: ErrorDetail) {
    super(detail.message)
    this.status = status
    this.code = detail.code
    this.fields = detail.fields ?? {}
    this.retryAfter = detail.retry_after
  }
}

const NETWORK_ERROR: ErrorDetail = {
  code: 'network_error',
  message: 'Impossible de joindre le serveur. Réessayez dans un instant.',
}

type ApiOptions = { method?: string; body?: unknown; signal?: AbortSignal }

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { method = 'GET', body, signal } = options
  // FormData (envoi de fichier) : le navigateur pose lui-même l'en-tête multipart.
  const json = body !== undefined && !(body instanceof FormData)
  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      method,
      signal,
      credentials: 'same-origin',
      headers: json ? { 'Content-Type': 'application/json' } : undefined,
      body: json ? JSON.stringify(body) : (body as FormData | undefined),
    })
  } catch (error) {
    // Requête annulée volontairement (la carte a bougé) : on laisse passer l'AbortError.
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(0, NETWORK_ERROR)
  }

  if (response.status === 204) {
    return undefined as T
  }
  const data: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = (data as { detail?: unknown } | null)?.detail
    const isDetail = typeof detail === 'object' && detail !== null && 'code' in detail
    throw new ApiError(response.status, isDetail ? (detail as ErrorDetail) : NETWORK_ERROR)
  }
  return data as T
}
