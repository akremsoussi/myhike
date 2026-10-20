import { CircleCheck } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { authApi } from '../../api/auth'
import { useAuth } from '../../auth/context'
import { Button, Notice, TextLink } from '../../components'
import { ApiError } from '../../lib/api'
import styles from './AuthForm.module.css'

type State = { kind: 'loading' } | { kind: 'confirmed' } | { kind: 'error'; message: string }

/** Page ouverte depuis le lien de l'email (/inscription/confirmer?token=…). */
export function ConfirmEmailPage() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const { me, refresh } = useAuth()
  const navigate = useNavigate()
  const [state, setState] = useState<State>(
    token ? { kind: 'loading' } : { kind: 'error', message: 'Ce lien est incomplet.' },
  )
  // En développement, StrictMode lance les effets deux fois : on ne confirme qu'une fois.
  const started = useRef(false)

  useEffect(() => {
    if (!token || started.current) return
    started.current = true
    authApi
      .verifyEmail(token)
      .then(async () => {
        // Connecté dans ce navigateur : on entre directement sur le site.
        const current = await refresh()
        if (current?.user.status === 'active') {
          navigate('/carte', { replace: true })
        } else {
          setState({ kind: 'confirmed' })
        }
      })
      .catch((err: unknown) => {
        setState({
          kind: 'error',
          message: err instanceof ApiError ? err.message : 'La confirmation a échoué. Réessayez.',
        })
      })
  }, [token, refresh, navigate])

  if (state.kind === 'loading') {
    return <p className={styles.subtitle}>Confirmation de votre adresse…</p>
  }

  if (state.kind === 'confirmed') {
    return (
      <div className={styles.form}>
        <h1 className={styles.title}>Adresse confirmée</h1>
        <Notice icon={<CircleCheck size={18} />}>Votre compte est activé. Connectez-vous pour accéder à Refuges.</Notice>
        <Button fullWidth onClick={() => navigate('/connexion')}>
          Se connecter
        </Button>
      </div>
    )
  }

  const pending = me?.user.status === 'pending_email'
  return (
    <div className={styles.form}>
      <h1 className={styles.title}>Lien non valide</h1>
      <Notice tone="danger">{state.message}</Notice>
      {pending ? (
        <TextLink to="/inscription/confirmation">Recevoir un nouveau lien</TextLink>
      ) : (
        <TextLink to="/connexion">Se connecter pour recevoir un nouveau lien</TextLink>
      )}
    </div>
  )
}
