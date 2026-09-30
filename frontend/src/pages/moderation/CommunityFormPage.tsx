import { ArrowLeft, Plus, Search, X } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { moderationApi, type ModCommunityDetail } from '../../api/moderation'
import { refugesApi, type Massif, type RefugeSummary } from '../../api/refuges'
import { Button, Card, Input, Notice, Select, Textarea } from '../../components'
import { api, ApiError } from '../../lib/api'
import { formatNumber } from '../../lib/format'
import styles from './CommunityFormPage.module.css'
import common from './moderation.module.css'

// Régions proposées, complétées par celles des communautés existantes.
const DEFAULT_REGIONS = ['Alpes', 'Préalpes', 'Pyrénées']
const FORM_ID = 'community-form'

/** Écran 15 · Créer (`/moderation/communautes/nouvelle`) ou modifier une communauté. */
export function CommunityFormPage() {
  const { slug } = useParams()
  const editing = slug !== undefined && slug !== 'nouvelle'
  return <CommunityForm key={slug ?? 'new'} slug={editing ? slug : null} />
}

function CommunityForm({ slug }: { slug: string | null }) {
  const navigate = useNavigate()
  const [loaded, setLoaded] = useState<ModCommunityDetail | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [region, setRegion] = useState('')
  const [massifId, setMassifId] = useState('')
  const [refuges, setRefuges] = useState<RefugeSummary[]>([])
  const [massifs, setMassifs] = useState<Massif[]>([])
  const [regions, setRegions] = useState(DEFAULT_REGIONS)
  const [adding, setAdding] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api<Massif[]>('/massifs').then(setMassifs).catch(() => undefined)
    moderationApi
      .communities()
      .then((list) => setRegions([...new Set([...DEFAULT_REGIONS, ...list.map((c) => c.region)])].sort((a, b) => a.localeCompare(b, 'fr'))))
      .catch(() => undefined)
  }, [])

  useEffect(() => {
    if (slug === null) return
    moderationApi
      .community(slug)
      .then((community) => {
        setLoaded(community)
        setName(community.name)
        setDescription(community.description)
        setRegion(community.region)
        setMassifId(community.massif ? String(community.massif.id) : '')
        setRefuges(community.refuges)
      })
      .catch((err: unknown) => setFormError(err instanceof ApiError ? err.message : 'La communauté n’a pas pu être chargée.'))
  }, [slug])

  async function submit(event: FormEvent) {
    event.preventDefault()
    const body = {
      name,
      description,
      region,
      massif_id: massifId ? Number(massifId) : null,
      refuge_ids: refuges.map((refuge) => refuge.id),
    }
    setSaving(true)
    setErrors({})
    setFormError(null)
    try {
      if (slug !== null) await moderationApi.updateCommunity(slug, body)
      else await moderationApi.createCommunity(body)
      navigate('/moderation/communautes')
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors(err.fields)
        setFormError(err.message)
      } else {
        setFormError('La communauté n’a pas pu être enregistrée.')
      }
    } finally {
      setSaving(false)
    }
  }

  async function remove() {
    if (!loaded || !window.confirm(`Supprimer définitivement « ${loaded.name} » ?`)) return
    try {
      await moderationApi.deleteCommunity(loaded.slug)
      navigate('/moderation/communautes')
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'La communauté n’a pas pu être supprimée.')
    }
  }

  const ready = slug === null || loaded !== null

  return (
    <div className={common.page}>
      <header className={common.header}>
        <div className={common.intro}>
          <Link to="/moderation/communautes" className={common.back}>
            <ArrowLeft aria-hidden size={14} />
            Communautés
          </Link>
          <h1 className={common.title}>{loaded ? `Modifier « ${loaded.name} »` : 'Nouvelle communauté'}</h1>
          <p className={common.lead}>
            {loaded ? 'Les modifications sont visibles immédiatement par les membres.' : 'Elle apparaîtra aussitôt dans l’onglet Communautés.'}
          </p>
        </div>
        <div className={common.headerActions}>
          <Button variant="secondary" onClick={() => navigate('/moderation/communautes')}>
            Annuler
          </Button>
          <Button type="submit" form={FORM_ID} disabled={saving || !ready}>
            {saving ? 'Enregistrement…' : loaded ? 'Enregistrer' : 'Créer la communauté'}
          </Button>
        </div>
      </header>

      {formError && <Notice tone="danger">{formError}</Notice>}

      <div className={`${common.columns} ${styles.columns}`}>
        <form id={FORM_ID} className={styles.form} onSubmit={(event) => void submit(event)} noValidate>
          <h2 className={common.sectionTitle}>Informations</h2>
          <Input label="Nom" value={name} maxLength={80} onChange={(e) => setName(e.target.value)} error={errors.name} disabled={!ready} />
          <Textarea
            label="Description"
            value={description}
            maxLength={2000}
            className={styles.description}
            onChange={(e) => setDescription(e.target.value)}
            error={errors.description}
            disabled={!ready}
          />
          <div className={styles.row}>
            <Input
              label="Région"
              list="regions"
              placeholder="Alpes, Pyrénées…"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              error={errors.region}
              disabled={!ready}
            />
            <datalist id="regions">
              {regions.map((item) => (
                <option key={item} value={item} />
              ))}
            </datalist>
            <Select
              label="Massif"
              value={massifId}
              onChange={(e) => setMassifId(e.target.value)}
              options={[{ value: '', label: 'Aucun' }, ...massifs.map((m) => ({ value: String(m.id), label: m.name }))]}
              disabled={!ready}
            />
            {/* Seul mode prévu par la maquette : pas de demande d'adhésion à valider. */}
            <Select label="Inscription" value="open" options={[{ value: 'open', label: 'Ouverte à tous' }]} disabled />
          </div>

          <div className={styles.field}>
            <span className={styles.label}>Refuges rattachés</span>
            <div className={styles.chips}>
              {refuges.map((refuge) => (
                <span key={refuge.id} className={styles.chip}>
                  {refuge.name}
                  <button
                    type="button"
                    className={styles.chipRemove}
                    aria-label={`Retirer ${refuge.name}`}
                    onClick={() => setRefuges((list) => list.filter((r) => r.id !== refuge.id))}
                  >
                    <X aria-hidden size={12} />
                  </button>
                </span>
              ))}
              <button type="button" className={styles.addChip} onClick={() => setAdding((value) => !value)} aria-expanded={adding}>
                <Plus aria-hidden size={12} /> Ajouter un refuge
              </button>
            </div>
            {errors.refuge_ids && <p className={styles.error}>{errors.refuge_ids}</p>}
            {adding && (
              <RefugePicker
                exclude={refuges.map((r) => r.id)}
                onPick={(refuge) => {
                  setRefuges((list) => [...list, refuge])
                  setAdding(false)
                }}
              />
            )}
          </div>
        </form>

        <div className={common.aside}>
          <Card padding="large" title={<span className={common.sectionTitle}>Visuels</span>}>
            {/* Pas encore de stockage d'images gratuit : zones réservées, comme dans la maquette. */}
            <span className={styles.label}>Bannière</span>
            <div className={styles.banner}>Bientôt : glisser une image ou parcourir</div>
            <span className={styles.label}>Icône</span>
            <div className={styles.iconRow}>
              <span className={styles.icon} aria-hidden />
              <Button size="sm" variant="secondary" disabled title="Bientôt disponible">
                Changer
              </Button>
            </div>
          </Card>

          {loaded && (
            <section className={styles.danger}>
              <h2 className={styles.dangerTitle}>Zone de danger</h2>
              <p className={common.muted}>
                La suppression retire définitivement la communauté, ses {formatNumber(loaded.post_count)} posts et désinscrit ses{' '}
                {formatNumber(loaded.member_count)} membres.
              </p>
              <Button variant="danger" fullWidth onClick={() => void remove()}>
                Supprimer la communauté
              </Button>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}

/** Recherche d'un refuge à rattacher. */
function RefugePicker({ exclude, onPick }: { exclude: number[]; onPick: (refuge: RefugeSummary) => void }) {
  const [search, setSearch] = useState('')
  const [results, setResults] = useState<RefugeSummary[]>([])
  const term = search.trim()

  useEffect(() => {
    if (term.length < 2) return
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      refugesApi
        .list({ q: term, limit: 8 }, controller.signal)
        .then((list) => setResults(list.items))
        .catch(() => undefined)
    }, 250)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [term])

  const shown = results.filter((refuge) => !exclude.includes(refuge.id))
  return (
    <div className={styles.picker}>
      <Input
        type="search"
        aria-label="Rechercher un refuge"
        placeholder="Rechercher un refuge…"
        icon={<Search aria-hidden size={16} />}
        value={search}
        autoFocus
        onChange={(e) => setSearch(e.target.value)}
      />
      {term.length >= 2 && (
        <ul className={styles.results}>
          {shown.map((refuge) => (
            <li key={refuge.id}>
              <button type="button" className={styles.result} onClick={() => onPick(refuge)}>
                {refuge.name}
                {refuge.massif && <span className={common.dim}> · {refuge.massif.name}</span>}
              </button>
            </li>
          ))}
          {shown.length === 0 && <li className={common.dim}>Aucun refuge trouvé.</li>}
        </ul>
      )}
    </div>
  )
}
