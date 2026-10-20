import { ArrowLeft, Globe, Lock, Plus, X } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { communitiesApi, postsApi, type PathPoint } from '../../api/communities'
import { mediaApi, type UploadedImage } from '../../api/media'
import { refugesApi } from '../../api/refuges'
import { usersApi } from '../../api/users'
import { Button, ChoiceCards, FileDrop, Notice, SegmentedControl, Select, Textarea, type Visibility } from '../../components'
import { ApiError } from '../../lib/api'
import { useApi } from '../../lib/useApi'
import styles from './NewPostPage.module.css'
import { PathField } from './PathField'
import { RefugeField, type ChosenRefuge } from './RefugeField'

type Destination = 'profile' | 'community'

const BODY_MAX_LENGTH = 5000
const MAX_PHOTOS = 4

/** Photo choisie : aperçu local tout de suite, `uploaded` une fois envoyée à l'API. */
type DraftPhoto = { preview: string; uploaded: UploadedImage | null }

/**
 * Écran 09 · Nouveau post. `?communaute=slug` présélectionne une communauté,
 * `?refuge=id` un refuge (bouton « Publier sur ce refuge » des posts liés).
 */
export function NewPostPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const requested = params.get('communaute')
  const requestedRefuge = Number(params.get('refuge')) || null

  const communities = useApi('communities', communitiesApi.list, 'Vos communautés n’ont pas pu être chargées.')
  // On ne peut publier que dans une communauté dont on est membre.
  const mine = (communities.data ?? []).filter((community) => community.is_member)

  const [destination, setDestination] = useState<Destination>(requested ? 'community' : 'profile')
  const [communitySlug, setCommunitySlug] = useState(requested ?? '')
  const [body, setBody] = useState('')
  // Visibilité par défaut choisie dans les paramètres (écran 05c), tant qu'on n'en change pas.
  const privacy = useApi('privacy', usersApi.privacy, 'Vos paramètres n’ont pas pu être chargés.')
  const [chosenVisibility, setVisibility] = useState<Visibility | null>(null)
  const visibility = chosenVisibility ?? privacy.data?.default_post_visibility ?? 'public'
  const [path, setPath] = useState<PathPoint[]>([])
  const [refuge, setRefuge] = useState<ChosenRefuge | null>(null)
  const [photos, setPhotos] = useState<DraftPhoto[]>([])
  const [photoError, setPhotoError] = useState<string | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const uploading = photos.some((photo) => photo.uploaded === null)

  useEffect(() => {
    if (requestedRefuge === null) return
    refugesApi
      .get(requestedRefuge)
      .then((found) => setRefuge((current) => current ?? { id: found.id, name: found.name }))
      .catch(() => undefined)
  }, [requestedRefuge])

  // Aperçus locaux (URL blob:) libérés en quittant la page.
  const previews = useRef(new Set<string>())
  useEffect(() => {
    const urls = previews.current
    return () => urls.forEach((url) => URL.revokeObjectURL(url))
  }, [])

  function addPhotos(files: File[]) {
    setPhotoError(null)
    const room = MAX_PHOTOS - photos.length
    if (files.length > room) setPhotoError(`${MAX_PHOTOS} photos au plus.`)
    for (const file of files.slice(0, Math.max(room, 0))) {
      const preview = URL.createObjectURL(file)
      previews.current.add(preview)
      setPhotos((list) => [...list, { preview, uploaded: null }])
      mediaApi
        .upload(file, 'photo')
        .then((uploaded) => setPhotos((list) => list.map((photo) => (photo.preview === preview ? { ...photo, uploaded } : photo))))
        .catch((err: unknown) => {
          removePhoto(preview)
          setPhotoError(err instanceof ApiError ? err.message : 'La photo n’a pas pu être envoyée.')
        })
    }
  }

  function removePhoto(preview: string) {
    setPhotos((list) => list.filter((photo) => photo.preview !== preview))
    URL.revokeObjectURL(preview)
    previews.current.delete(preview)
  }

  // Communauté demandée dans l'URL mais pas (ou plus) rejointe : on prend la première.
  const selectedSlug = mine.some((community) => community.slug === communitySlug) ? communitySlug : (mine[0]?.slug ?? '')
  const origin = mine.find((community) => community.slug === requested)
  const backUrl = origin
    ? `/communautes/${origin.slug}`
    : requestedRefuge !== null
      ? `/refuges/${requestedRefuge}/posts`
      : '/communautes'

  async function submit(event: FormEvent) {
    event.preventDefault()
    const text = body.trim()
    if (!text && photos.length === 0 && path.length === 0) {
      setErrors({ body: 'Écrivez quelques mots, ajoutez une photo ou un chemin.' })
      return
    }
    if (path.length === 1) {
      setErrors({ path: 'Ajoutez au moins un deuxième point, ou effacez le chemin.' })
      return
    }
    if (destination === 'community' && !selectedSlug) {
      setErrors({ community: 'Choisissez une communauté.' })
      return
    }
    setSubmitting(true)
    setErrors({})
    setFormError(null)
    try {
      const post = await postsApi.create({
        body: text,
        visibility,
        community_slug: destination === 'community' ? selectedSlug : undefined,
        photo_ids: photos.flatMap((photo) => (photo.uploaded ? [photo.uploaded.id] : [])),
        path: path.length >= 2 ? path : undefined,
        refuge_id: refuge?.id,
      })
      navigate(
        post.community
          ? `/communautes/${post.community.slug}`
          : post.refuge && post.refuge.id === requestedRefuge
            ? `/refuges/${post.refuge.id}/posts`
            : '/profil',
      )
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors({
          body: err.fields.body,
          community: err.fields.community_slug,
          path: err.fields.path,
          refuge: err.fields.refuge_id,
        })
        if (err.fields.photo_ids) setPhotoError(err.fields.photo_ids)
        setFormError(err.message)
      } else {
        setFormError('Le post n’a pas pu être publié.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.page}>
      <Link to={backUrl} className={styles.back}>
        <ArrowLeft aria-hidden size={14} />
        {origin ? origin.name : requestedRefuge !== null ? 'Posts liés au refuge' : 'Communautés'}
      </Link>
      <h1 className={styles.title}>Nouveau post</h1>

      <form className={styles.card} onSubmit={(event) => void submit(event)} noValidate>
        {formError && <Notice tone="danger">{formError}</Notice>}
        <div className={styles.columns}>
          <div className={styles.column}>
            <div className={styles.field}>
              <span id="destination-label" className={styles.label}>
                Publier sur
              </span>
              <SegmentedControl
                fullWidth
                aria-label="Publier sur"
                value={destination}
                onChange={setDestination}
                segments={[
                  { value: 'profile', label: 'Mon profil' },
                  { value: 'community', label: 'Une communauté' },
                ]}
              />
              {destination === 'community' &&
                (mine.length > 0 ? (
                  <Select
                    aria-labelledby="destination-label"
                    value={selectedSlug}
                    onChange={(event) => setCommunitySlug(event.target.value)}
                    options={mine.map((community) => ({ value: community.slug, label: community.name }))}
                    error={errors.community}
                    hint="Le post apparaîtra dans la communauté et sur votre profil."
                  />
                ) : (
                  !communities.loading && (
                    <p className={styles.hint}>
                      Vous n’avez rejoint aucune communauté.{' '}
                      <Link to="/communautes" className={styles.link}>
                        Voir les communautés
                      </Link>
                    </p>
                  )
                ))}
              {destination === 'profile' && <p className={styles.hint}>Le post apparaîtra seulement sur votre profil.</p>}
            </div>

            <Textarea
              label="Description"
              placeholder="Racontez votre sortie, les conditions, vos conseils…"
              value={body}
              maxLength={BODY_MAX_LENGTH}
              onChange={(event) => setBody(event.target.value)}
              error={errors.body}
            />

            <div className={styles.field}>
              <span className={styles.label}>Photos</span>
              <div className={styles.photos}>
                {photos.map((photo, index) => (
                  <div key={photo.preview} className={styles.photo}>
                    <img
                      src={photo.preview}
                      alt={`Photo ${index + 1}`}
                      className={photo.uploaded ? styles.photoImage : `${styles.photoImage} ${styles.sending}`}
                    />
                    <button
                      type="button"
                      className={styles.removePhoto}
                      aria-label={`Retirer la photo ${index + 1}`}
                      onClick={() => removePhoto(photo.preview)}
                    >
                      <X aria-hidden size={12} />
                    </button>
                  </div>
                ))}
                {photos.length < MAX_PHOTOS && (
                  <FileDrop multiple onFiles={addPhotos} aria-label="Ajouter des photos" className={styles.addPhoto}>
                    <Plus aria-hidden size={14} />
                    Ajouter
                  </FileDrop>
                )}
              </div>
              {photoError ? (
                <p className={styles.error} role="alert">
                  {photoError}
                </p>
              ) : (
                <p className={styles.hint}>
                  {uploading ? 'Envoi des photos…' : `JPEG, PNG ou WebP, ${MAX_PHOTOS} au plus. La position GPS des photos est retirée.`}
                </p>
              )}
            </div>
          </div>

          <div className={styles.column}>
            <div className={styles.field}>
              <span className={styles.label}>Chemin (optionnel)</span>
              <PathField path={path} onChange={setPath} error={errors.path} />
            </div>

            <div className={styles.field}>
              <span className={styles.label}>Refuge (optionnel)</span>
              <RefugeField value={refuge} onChange={setRefuge} error={errors.refuge} />
            </div>

            <div className={styles.field}>
              <span className={styles.label}>Visibilité</span>
              <ChoiceCards
                aria-label="Visibilité"
                value={visibility}
                onChange={setVisibility}
                choices={[
                  {
                    value: 'public',
                    label: 'Public',
                    description: 'Visible par tous les membres',
                    icon: <Globe aria-hidden size={15} />,
                  },
                  {
                    value: 'friends',
                    label: 'Amis uniquement',
                    description: 'Visible seulement par vos amis',
                    icon: <Lock aria-hidden size={15} />,
                  },
                ]}
              />
            </div>
          </div>
        </div>

        <div className={styles.actions}>
          <Button variant="secondary" onClick={() => navigate(backUrl)}>
            Annuler
          </Button>
          <Button type="submit" disabled={submitting || uploading}>
            {submitting ? 'Publication…' : uploading ? 'Envoi des photos…' : 'Publier'}
          </Button>
        </div>
      </form>
    </div>
  )
}
