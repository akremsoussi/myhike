import { MailCheck } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { authApi } from '../../api/auth'
import { Button, Input, Notice, TextLink } from '../../components'
import { ApiError } from '../../lib/api'
import styles from './AuthForm.module.css'

/** « Mot de passe oublié ? » (lien de l'écran 01) : demande d'un lien par email. */
export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sentTo, setSentTo] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const address = email.trim()
    if (!address.includes('@')) {
      setError('Renseignez l’adresse email de votre compte.')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      await authApi.requestPasswordReset(address)
      setSentTo(address)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Une erreur est survenue. Réessayez.')
    } finally {
      setSubmitting(false)
    }
  }

  if (sentTo) {
    // Même message qu'il existe un compte ou non : on ne révèle pas quelles adresses sont inscrites.
    return (
      <div className={styles.form}>
        <h1 className={styles.title}>Vérifiez vos emails</h1>
        <Notice icon={<MailCheck size={18} />}>
          Si un compte existe pour <strong>{sentTo}</strong>, vous allez recevoir un lien pour choisir un nouveau mot de
          passe. Il expire au bout d’une heure.
        </Notice>
        <p className={styles.subtitle}>Rien reçu ? Regardez dans les indésirables, ou réessayez dans une minute.</p>
        <Button variant="secondary" fullWidth onClick={() => setSentTo(null)}>
          Utiliser une autre adresse
        </Button>
        <TextLink to="/connexion">← Retour à la connexion</TextLink>
      </div>
    )
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <h1 className={styles.title}>Mot de passe oublié</h1>
      <p className={styles.subtitle}>Indiquez l’adresse de votre compte : nous vous enverrons un lien pour en choisir un nouveau.</p>
      <Input
        label="Email"
        type="email"
        autoComplete="email"
        placeholder="nom@exemple.com"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        required
      />
      {error && <Notice tone="danger">{error}</Notice>}
      <Button type="submit" fullWidth disabled={submitting}>
        Envoyer le lien
      </Button>
      <TextLink to="/connexion">← Retour à la connexion</TextLink>
    </form>
  )
}
