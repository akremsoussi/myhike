import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from './context'

const PENDING_PAGE = '/inscription/confirmation'
const HOME = '/carte'

type FromState = { from?: string } | null

/** Pages du site : compte confirmé obligatoire. */
export function RequireActive() {
  const { me } = useAuth()
  const location = useLocation()
  if (me === undefined) return null
  if (me === null) {
    return <Navigate to="/connexion" replace state={{ from: location.pathname + location.search }} />
  }
  if (me.user.status !== 'active') return <Navigate to={PENDING_PAGE} replace />
  return <Outlet />
}

/** Écrans de modération. À placer sous RequireActive. */
export function RequireModerator() {
  const { me } = useAuth()
  if (me?.user.role !== 'moderator') return <Navigate to={HOME} replace />
  return <Outlet />
}

/** Écran 02b : seulement pour un compte connecté qui n'a pas confirmé son adresse. */
export function RequirePending() {
  const { me } = useAuth()
  if (me === undefined) return null
  if (me === null) return <Navigate to="/connexion" replace />
  if (me.user.status === 'active') return <Navigate to={HOME} replace />
  return <Outlet />
}

/** Connexion et inscription : un utilisateur déjà connecté est renvoyé là où il allait. */
export function GuestOnly() {
  const { me } = useAuth()
  const from = (useLocation().state as FromState)?.from
  if (me === undefined) return null
  if (me === null) return <Outlet />
  if (me.user.status !== 'active') return <Navigate to={PENDING_PAGE} replace />
  return <Navigate to={from ?? HOME} replace />
}
