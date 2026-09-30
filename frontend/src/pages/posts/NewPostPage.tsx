import { ArrowLeft, Globe, Lock, Plus } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { communitiesApi, postsApi } from '../../api/communities'
import { usersApi } from '../../api/users'
import { Button, ChoiceCards, Notice, SegmentedControl, Select, Textarea, type Visibility } from '../../components'
import { ApiError } from '../../lib/api'
import { useApi } from '../../lib/useApi'
import styles from './NewPostPage.module.css'

type Destination = 'profile' | 'community'

const BODY_MAX_LENGTH = 5000

/** Écran 09 · Nouveau post. `?communaute=slug` présélectionne une communauté. */
export function NewPostPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const requested = params.get('communaute')

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
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Communauté demandée dans l'URL mais pas (ou plus) rejointe : on prend la première.
  const selectedSlug = mine.some((community) => community.slug === communitySlug) ? communitySlug : (mine[0]?.slug ?? '')
  const origin = mine.find((community) => community.slug === requested)
  const backUrl = origin ? `/communautes/${origin.slug}` : '/communautes'

  async function submit(event: FormEvent) {
    event.preventDefault()
    const text = body.trim()
    if (!text) {
      setErrors({ body: 'Écrivez quelques mots.' })
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
      })
      navigate(post.community ? `/communautes/${post.community.slug}` : '/profil')
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors({ body: err.fields.body, community: err.fields.community_slug })
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
        {origin ? origin.name : 'Communautés'}
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
                <button type="button" className={styles.addPhoto} disabled title="Bientôt disponible">
                  <Plus aria-hidden size={14} />
                  Ajouter
                </button>
              </div>
            </div>
          </div>

          <div className={styles.column}>
            <div className={styles.field}>
              <span className={styles.label}>Chemin (optionnel)</span>
              {/* Tracé et import GPX : pas encore disponibles, zone réservée comme dans la maquette. */}
              <div className={styles.map}>Bientôt : tracez ou importez votre chemin</div>
              <div className={styles.pathButtons}>
                <Button variant="secondary" fullWidth disabled>
                  Tracer sur la carte
                </Button>
                <Button variant="secondary" fullWidth disabled>
                  Importer un GPX
                </Button>
              </div>
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
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Publication…' : 'Publier'}
          </Button>
        </div>
      </form>
    </div>
  )
}
