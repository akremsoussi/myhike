import { Search } from 'lucide-react'
import { useState } from 'react'
import { communitiesApi, type Community } from '../../api/communities'
import { Chip, CommunityCard, Input, Notice } from '../../components'
import { ApiError } from '../../lib/api'
import { useApi } from '../../lib/useApi'
import styles from './CommunitiesPage.module.css'

const ALL = 'all'
const MINE = 'mine'

/** Recherche insensible à la casse et aux accents (« ecrins » trouve « Écrins »). */
function normalize(text: string): string {
  return text.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase()
}

/** Écran 07 · Communautés. */
export function CommunitiesPage() {
  const { data, error, loading, setData } = useApi('communities', communitiesApi.list, 'Les communautés n’ont pas pu être chargées.')
  const [filter, setFilter] = useState(ALL)
  const [search, setSearch] = useState('')
  const [busySlug, setBusySlug] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const communities = data ?? []
  // Les régions viennent des données : une nouvelle région apparaît sans changer le code.
  const regions = [...new Set(communities.map((community) => community.region))].sort((a, b) => a.localeCompare(b, 'fr'))
  const term = normalize(search.trim())
  const visible = communities.filter((community) => {
    if (filter === MINE && !community.is_member) return false
    if (filter !== ALL && filter !== MINE && community.region !== filter) return false
    return !term || normalize(`${community.name} ${community.massif?.name ?? ''}`).includes(term)
  })

  async function toggleMembership(community: Community) {
    setBusySlug(community.slug)
    setActionError(null)
    try {
      const updated = community.is_member
        ? await communitiesApi.leave(community.slug)
        : await communitiesApi.join(community.slug)
      setData((list) => list?.map((item) => (item.slug === updated.slug ? updated : item)) ?? null)
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'L’action n’a pas pu aboutir.')
    } finally {
      setBusySlug(null)
    }
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.intro}>
          <h1 className={styles.title}>Communautés</h1>
          <p className={styles.lead}>Rejoignez les communautés de vos massifs pour partager chemins et photos.</p>
        </div>
        <div className={styles.search}>
          <Input
            type="search"
            aria-label="Rechercher une communauté"
            placeholder="Rechercher une communauté"
            icon={<Search aria-hidden size={16} />}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
      </header>

      <div className={styles.filters} role="group" aria-label="Filtrer les communautés">
        <Chip selected={filter === ALL} onClick={() => setFilter(ALL)}>
          Toutes
        </Chip>
        <Chip selected={filter === MINE} onClick={() => setFilter(MINE)}>
          Mes communautés
        </Chip>
        {regions.map((region) => (
          <Chip key={region} selected={filter === region} onClick={() => setFilter(region)}>
            {region}
          </Chip>
        ))}
      </div>

      {error && <Notice tone="danger">{error}</Notice>}
      {actionError && <Notice tone="danger">{actionError}</Notice>}

      <div className={styles.grid}>
        {visible.map((community) => (
          <CommunityCard
            key={community.slug}
            community={community}
            busy={busySlug === community.slug}
            onToggleMembership={() => void toggleMembership(community)}
          />
        ))}
      </div>

      {!loading && !error && visible.length === 0 && (
        <p className={styles.empty}>
          {filter === MINE && !term
            ? 'Vous n’avez rejoint aucune communauté pour l’instant.'
            : 'Aucune communauté ne correspond à cette recherche.'}
        </p>
      )}
    </div>
  )
}
