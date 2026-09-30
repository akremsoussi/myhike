import { useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { authApi } from '../../api/auth'
import { useAuth } from '../../auth/context'
import { Button, Checkbox, Input, Notice } from '../../components'
import { ApiError } from '../../lib/api'
import styles from './AuthForm.module.css'

const USERNAME_RE = /^[a-z0-9_]{3,30}$/
const PASSWORD_MIN_LENGTH = 8

type Field = 'username' | 'email' | 'password' | 'confirmation' | 'accept_terms'
type Errors = Partial<Record<Field, string>>

function validate(values: Record<Exclude<Field, 'accept_terms'>, string> & { accept_terms: boolean }): Errors {
  const errors: Errors = {}
  if (!USERNAME_RE.test(values.username.trim().toLowerCase())) {
    errors.username = '3 à 30 caractères : lettres minuscules, chiffres ou « _ ».'
  }
  if (!/^\S+@\S+\.\S+$/.test(values.email.trim())) {
    errors.email = 'Adresse email invalide.'
  }
  if (values.password.length < PASSWORD_MIN_LENGTH) {
    errors.password = `${PASSWORD_MIN_LENGTH} caractères min.`
  }
  if (values.confirmation !== values.password) {
    errors.confirmation = 'Les mots de passe ne correspondent pas.'
  }
  if (!values.accept_terms) {
    errors.accept_terms = "Vous devez accepter les conditions d'utilisation."
  }
  return errors
}

/** Écran 02 · Inscription. */
export function RegisterPage() {
  const { setMe } = useAuth()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [acceptTerms, setAcceptTerms] = useState(false)
  const [errors, setErrors] = useState<Errors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)
    const found = validate({ username, email, password, confirmation, accept_terms: acceptTerms })
    setErrors(found)
    if (Object.keys(found).length > 0) return

    setSubmitting(true)
    try {
      // Compte créé et connecté : le garde GuestOnly affiche l'écran 02b.
      setMe(await authApi.register({ username, email, password, accept_terms: acceptTerms }))
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fields).length > 0) {
        setErrors(err.fields as Errors)
      } else {
        setFormError(err instanceof ApiError ? err.message : 'Une erreur est survenue. Réessayez.')
      }
      setSubmitting(false)
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <h1 className={styles.title}>Créer un compte</h1>
      <Input
        label="Nom d'utilisateur"
        autoComplete="username"
        placeholder="camille_m"
        value={username}
        onChange={(event) => setUsername(event.target.value)}
        error={errors.username}
      />
      <Input
        label="Email"
        type="email"
        autoComplete="email"
        placeholder="nom@exemple.com"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        error={errors.email}
      />
      <div className={styles.pair}>
        <Input
          label="Mot de passe"
          type="password"
          autoComplete="new-password"
          placeholder="8 caractères min."
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={errors.password}
        />
        <Input
          label="Confirmation"
          type="password"
          autoComplete="new-password"
          placeholder="••••••••"
          value={confirmation}
          onChange={(event) => setConfirmation(event.target.value)}
          error={errors.confirmation}
        />
      </div>
      <Checkbox
        checked={acceptTerms}
        onChange={(event) => setAcceptTerms(event.target.checked)}
        error={errors.accept_terms}
      >
        J'accepte les{' '}
        <Link to="/conditions" className={styles.inlineLink}>
          conditions d'utilisation
        </Link>
      </Checkbox>
      {formError && <Notice tone="danger">{formError}</Notice>}
      <Button type="submit" fullWidth disabled={submitting}>
        S'inscrire
      </Button>
      <p className={styles.footer}>
        Déjà un compte ?
        <Link to="/connexion" className={styles.inlineLink}>
          Se connecter
        </Link>
      </p>
    </form>
  )
}
