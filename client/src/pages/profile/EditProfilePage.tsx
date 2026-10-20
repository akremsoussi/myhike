import { ArrowLeft } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { usersApi, type EditableProfile } from '../../api/users'
import { useAuth } from '../../auth/context'
import { Avatar, Button, Input, Notice, Textarea } from '../../components'
import { ApiError } from '../../lib/api'
import { useApi } from '../../lib/useApi'
import styles from './EditProfilePage.module.css'

const DISPLAY_NAME_MAX_LENGTH = 60
const BIO_MAX_LENGTH = 300

/** « Modifier le profil » (bouton de l'écran 05) : nom affiché et présentation. */
export function EditProfilePage() {
  const saved = useApi('my-profile', usersApi.myProfile, 'Votre profil n’a pas pu être chargé.')
  if (!saved.data) {
    return <div className={styles.page}>{saved.error && <Notice tone="danger">{saved.error}</Notice>}</div>
  }
  return <EditProfileForm initial={saved.data} />
}

function EditProfileForm({ initial }: { initial: EditableProfile }) {
  const { me, refresh } = useAuth()
  const navigate = useNavigate()
  const [displayName, setDisplayName] = useState(initial.display_name)
  const [bio, setBio] = useState(initial.bio)
  const [errors, setErrors] = useState<{ display_name?: string; bio?: string }>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    const name = displayName.trim()
    if (name.length < 2) {
      setErrors({ display_name: `2 à ${DISPLAY_NAME_MAX_LENGTH} caractères.` })
      return
    }
    setErrors({})
    setFormError(null)
    setSaving(true)
    try {
      await usersApi.updateMyProfile({ display_name: name, bio })
      // Le nom apparaît aussi dans la barre de navigation.
      await refresh()
      navigate('/profil')
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors({ display_name: err.fields.display_name, bio: err.fields.bio })
        setFormError(err.message)
      } else {
        setFormError('Votre profil n’a pas pu être enregistré.')
      }
      setSaving(false)
    }
  }

  return (
    <div className={styles.page}>
      <Link to="/profil" className={styles.back}>
        <ArrowLeft aria-hidden size={14} />
        Mon profil
      </Link>
      <h1 className={styles.title}>Modifier le profil</h1>

      <form className={styles.card} onSubmit={(event) => void submit(event)} noValidate>
        {formError && <Notice tone="danger">{formError}</Notice>}
        <div className={styles.identity}>
          <Avatar name={displayName.trim() || initial.display_name} size="6xl" />
          <div>
            <p className={styles.name}>{displayName.trim() || initial.display_name}</p>
            <p className={styles.muted}>@{me?.user.username} · le nom d’utilisateur ne change pas</p>
          </div>
        </div>
        <Input
          label="Nom affiché"
          autoComplete="name"
          placeholder="Camille Martin"
          value={displayName}
          maxLength={DISPLAY_NAME_MAX_LENGTH}
          onChange={(event) => setDisplayName(event.target.value)}
          error={errors.display_name}
          hint="Visible sur votre profil, vos posts et vos sorties."
        />
        <Textarea
          label="Présentation"
          placeholder="Votre pratique, vos massifs préférés, vos prochains projets…"
          value={bio}
          maxLength={BIO_MAX_LENGTH}
          onChange={(event) => setBio(event.target.value)}
          error={errors.bio}
          hint={`${bio.length} / ${BIO_MAX_LENGTH}`}
        />
        <div className={styles.actions}>
          <Button variant="secondary" onClick={() => navigate('/profil')}>
            Annuler
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? 'Enregistrement…' : 'Enregistrer'}
          </Button>
        </div>
      </form>
    </div>
  )
}
