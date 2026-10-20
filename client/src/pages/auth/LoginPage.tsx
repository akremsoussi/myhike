import { useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { authApi } from '../../api/auth'
import { useAuth } from '../../auth/context'
import { Button, Input, Notice, TextLink } from '../../components'
import { ApiError } from '../../lib/api'
import styles from './AuthForm.module.css'

/** Écran 01 · Connexion. */
export function LoginPage() {
  const { setMe } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!email.trim() || !password) {
      setError('Renseignez votre email et votre mot de passe.')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      // Le garde GuestOnly redirige ensuite : vers la page demandée, /carte ou l'écran 02b.
      setMe(await authApi.login(email, password))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Une erreur est survenue. Réessayez.')
      setSubmitting(false)
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <h1 className={styles.title}>Connexion</h1>
      <p className={styles.subtitle}>
        Heureux de vous revoir. Connectez-vous pour accéder à vos communautés et sorties.
      </p>
      <Input
        label="Email"
        type="email"
        autoComplete="email"
        placeholder="nom@exemple.com"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        required
      />
      <Input
        label="Mot de passe"
        type="password"
        autoComplete="current-password"
        placeholder="••••••••"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        required
      />
      <TextLink to="/mot-de-passe-oublie">Mot de passe oublié ?</TextLink>
      {error && <Notice tone="danger">{error}</Notice>}
      <Button type="submit" fullWidth disabled={submitting}>
        Se connecter
      </Button>
      <p className={styles.footer}>
        Pas encore de compte ?
        <Link to="/inscription" className={styles.inlineLink}>
          Créer un compte
        </Link>
      </p>
    </form>
  )
}
