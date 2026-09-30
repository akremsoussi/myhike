import { Check, Mail } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { authApi } from '../../api/auth'
import { useAuth } from '../../auth/context'
import { Button, Input, Notice, StatusBadge, TextLink } from '../../components'
import { ApiError } from '../../lib/api'
import { cx } from '../../lib/cx'
import { formatCountdown, formatDayTime } from '../../lib/format'
import styles from './PendingPage.module.css'

// Toutes les 5 s, on vérifie si l'adresse a été confirmée (lien ouvert dans un autre onglet).
const POLL_INTERVAL_MS = 5000

type StepState = 'done' | 'current' | 'upcoming'

function Step({ state, title, detail }: { state: StepState; title: string; detail: string }) {
  return (
    <li className={cx(styles.step, styles[state])}>
      <span className={styles.stepIcon} aria-hidden>
        {state === 'done' && <Check size={14} strokeWidth={3} />}
      </span>
      <div className={styles.stepText}>
        <span className={styles.stepTitle}>{title}</span>
        <span className={styles.stepDetail}>{detail}</span>
      </div>
    </li>
  )
}

function useNow(): number {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [])
  return now
}

/** Écran 02b · Compte en attente de confirmation de l'adresse email. */
export function PendingPage() {
  const { me, setMe, refresh, logout } = useAuth()
  const now = useNow()
  const [error, setError] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const [editing, setEditing] = useState(false)
  const [newEmail, setNewEmail] = useState('')
  const [emailError, setEmailError] = useState<string | undefined>()

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') {
        refresh().catch(() => undefined)
      }
    }, POLL_INTERVAL_MS)
    return () => window.clearInterval(timer)
  }, [refresh])

  // Le garde RequirePending garantit un compte connecté et non confirmé.
  if (!me) return null
  const { user, verification } = me
  const email = verification?.email ?? user.email
  const waitSeconds = verification ? (new Date(verification.resend_available_at).getTime() - now) / 1000 : 0
  const canResend = waitSeconds <= 0

  async function resend() {
    setError(null)
    setSending(true)
    try {
      setMe(await authApi.resendVerification())
    } catch (err) {
      if (err instanceof ApiError && err.code === 'resend_too_soon') {
        await refresh()
      } else {
        setError(err instanceof ApiError ? err.message : "L'email n'a pas pu être renvoyé.")
      }
    } finally {
      setSending(false)
    }
  }

  async function changeEmail(event: FormEvent) {
    event.preventDefault()
    setEmailError(undefined)
    try {
      setMe(await authApi.changePendingEmail(newEmail))
      setEditing(false)
      setNewEmail('')
    } catch (err) {
      setEmailError(err instanceof ApiError ? (err.fields.email ?? err.message) : "L'adresse n'a pas pu être modifiée.")
    }
  }

  return (
    <div className={styles.page}>
      <span className={styles.envelope} aria-hidden>
        <Mail size={30} strokeWidth={2} />
      </span>

      <header className={styles.header}>
        <StatusBadge tone="pending" icon={<span className={styles.dot} />}>
          En attente de confirmation
        </StatusBadge>
        <h1 className={styles.title}>Vérifiez votre boîte mail</h1>
        <p className={styles.text}>
          Nous avons envoyé un lien de confirmation à <strong className={styles.email}>{email}</strong>. Cliquez
          dessus pour activer votre compte et accéder à Refuges.
        </p>
      </header>

      <ol className={styles.steps}>
        <Step state="done" title="Compte créé" detail={formatDayTime(user.created_at)} />
        <Step state="current" title="Adresse email à confirmer" detail="En attente de votre clic sur le lien" />
        <Step state="upcoming" title="Accès à Refuges" detail="Carte, communautés, sorties et amis" />
      </ol>

      <div className={styles.actions}>
        <Button variant="secondary" fullWidth onClick={resend} disabled={!canResend || sending}>
          Renvoyer l'email
        </Button>
        <p className={styles.hint}>
          {canResend
            ? 'Le lien expire dans 24 h'
            : `Vous pourrez renvoyer un email dans ${formatCountdown(waitSeconds)} · le lien expire dans 24 h`}
        </p>
        {error && <Notice tone="danger">{error}</Notice>}
      </div>

      {editing ? (
        <form className={styles.changeEmail} onSubmit={changeEmail} noValidate>
          <Input
            label="Nouvelle adresse email"
            type="email"
            autoComplete="email"
            placeholder="nom@exemple.com"
            value={newEmail}
            onChange={(event) => setNewEmail(event.target.value)}
            error={emailError}
            autoFocus
          />
          <div className={styles.changeEmailActions}>
            <Button size="sm" variant="secondary" onClick={() => setEditing(false)}>
              Annuler
            </Button>
            <Button size="sm" type="submit" disabled={!newEmail}>
              Envoyer le lien
            </Button>
          </div>
        </form>
      ) : (
        <p className={styles.links}>
          Mauvaise adresse ?
          <TextLink onClick={() => setEditing(true)}>Modifier l'email</TextLink>
        </p>
      )}

      <TextLink onClick={() => void logout()}>← Retour à la connexion</TextLink>
      <p className={styles.hint}>Rien reçu ? Pensez à vérifier vos courriers indésirables.</p>
    </div>
  )
}
