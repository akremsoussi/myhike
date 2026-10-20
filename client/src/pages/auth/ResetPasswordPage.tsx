import { CircleCheck } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { authApi } from '../../api/auth'
import { useAuth } from '../../auth/context'
import { Button, Input, Notice, TextLink } from '../../components'
import { ApiError } from '../../lib/api'
import styles from './AuthForm.module.css'

const PASSWORD_MIN_LENGTH = 8

/** Page ouverte depuis l'email « Mot de passe oublié » (/mot-de-passe/nouveau?token=…). */
export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const { setMe } = useAuth()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [errors, setErrors] = useState<{ password?: string; confirmation?: string }>({})
  const [linkError, setLinkError] = useState<string | null>(token ? null : 'Ce lien est incomplet.')
  const [formError, setFormError] = useState<string | null>(null)
  const [done, setDone] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!token) return
    const found: typeof errors = {}
    if (password.length < PASSWORD_MIN_LENGTH) found.password = `${PASSWORD_MIN_LENGTH} caractères min.`
    if (confirmation !== password) found.confirmation = 'Les deux mots de passe ne correspondent pas.'
    setErrors(found)
    if (Object.keys(found).length > 0) return
    setFormError(null)
    setSubmitting(true)
    try {
      await authApi.resetPassword(token, password)
      // Toutes les sessions sont fermées, celle de ce navigateur aussi.
      setMe(null)
      setDone(true)
    } catch (err) {
      if (err instanceof ApiError && (err.code === 'invalid_token' || err.code === 'token_expired')) {
        setLinkError(err.message)
      } else if (err instanceof ApiError && err.fields.password) {
        setErrors({ password: err.fields.password })
      } else {
        setFormError(err instanceof ApiError ? err.message : 'Une erreur est survenue. Réessayez.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (done) {
    return (
      <div className={styles.form}>
        <h1 className={styles.title}>Mot de passe changé</h1>
        <Notice icon={<CircleCheck size={18} />}>
          Votre nouveau mot de passe est enregistré. Par sécurité, vous avez été déconnecté de tous vos appareils.
        </Notice>
        <Button fullWidth onClick={() => navigate('/connexion')}>
          Se connecter
        </Button>
      </div>
    )
  }

  if (linkError) {
    return (
      <div className={styles.form}>
        <h1 className={styles.title}>Lien non valide</h1>
        <Notice tone="danger">{linkError}</Notice>
        <TextLink to="/mot-de-passe-oublie">Recevoir un nouveau lien</TextLink>
      </div>
    )
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <h1 className={styles.title}>Nouveau mot de passe</h1>
      <p className={styles.subtitle}>Choisissez un mot de passe que vous n’utilisez pas ailleurs.</p>
      <Input
        label="Nouveau mot de passe"
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
      {formError && <Notice tone="danger">{formError}</Notice>}
      <Button type="submit" fullWidth disabled={submitting}>
        Enregistrer
      </Button>
      <TextLink to="/connexion">← Retour à la connexion</TextLink>
    </form>
  )
}
