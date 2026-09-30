import { Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { moderationApi, type ModCommunity } from '../../api/moderation'
import { Button, ButtonLink, Chip, Input, Notice } from '../../components'
import { ApiError } from '../../lib/api'
import { formatCount, formatDate, formatNumber } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import styles from './CommunitiesAdminPage.module.css'
import common from './moderation.module.css'

const ALL = 'all'

function normalize(text: string): string {
  return text.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase()
}

/** Écran 14 · Gestion des communautés. */
export function CommunitiesAdminPage() {
  const communities = useApi('mod-communities', moderationApi.communities, 'Les communautés n’ont pas pu être chargées.')
  const [search, setSearch] = useState('')
  const [region, setRegion] = useState(ALL)
  const [error, setError] = useState<string | null>(null)

  const all = communities.data ?? []
  const regions = [...new Set(all.map((c) => c.region))].sort((a, b) => a.localeCompare(b, 'fr'))
  const term = normalize(search.trim())
  const shown = all.filter(
    (c) => (region === ALL || c.region === region) && (!term || normalize(`${c.name} ${c.massif?.name ?? ''}`).includes(term)),
  )

  async function remove(community: ModCommunity) {
    const message =
      `Supprimer « ${community.name} » ? Ses ${formatNumber(community.post_count)} posts seront supprimés ` +
      `et ses ${formatNumber(community.member_count)} membres désinscrits.`
    if (!window.confirm(message)) return
    setError(null)
    try {
      await moderationApi.deleteCommunity(community.slug)
      communities.setData((list) => list?.filter((c) => c.slug !== community.slug) ?? null)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'La communauté n’a pas pu être supprimée.')
    }
  }

  return (
    <div className={common.page}>
      <header className={common.header}>
        <div className={common.intro}>
          <h1 className={common.title}>Communautés</h1>
          <p className={common.lead}>{formatCount(all.length, 'communauté')}</p>
        </div>
        <ButtonLink to="/moderation/communautes/nouvelle" icon={<Plus aria-hidden size={16} />}>
          Créer une communauté
        </ButtonLink>
      </header>

      <div className={common.toolbar}>
        <div className={common.search}>
          <Input
            type="search"
            aria-label="Rechercher une communauté"
            placeholder="Rechercher une communauté"
            icon={<Search aria-hidden size={16} />}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <div className={common.toolbar} role="group" aria-label="Filtrer par région">
          <Chip size="sm" selected={region === ALL} onClick={() => setRegion(ALL)}>
            Toutes
          </Chip>
          {regions.map((item) => (
            <Chip key={item} size="sm" selected={region === item} onClick={() => setRegion(item)}>
              {item}
            </Chip>
          ))}
        </div>
      </div>

      {(communities.error || error) && <Notice tone="danger">{communities.error ?? error}</Notice>}

      <div className={common.tableCard}>
        <table className={common.table}>
          <thead>
            <tr>
              <th>Communauté</th>
              <th className={styles.region}>Région</th>
              <th className={styles.members}>Membres</th>
              <th className={styles.posts}>Posts</th>
              <th className={styles.created}>Créée le</th>
              <th className={styles.actions}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((community) => (
              <tr key={community.slug}>
                <td>
                  <span className={styles.name}>
                    {/* Pas encore d'icône : zone réservée, comme dans la maquette. */}
                    <span className={styles.thumb} aria-hidden />
                    {community.name}
                  </span>
                </td>
                <td>{community.region}</td>
                <td>{formatNumber(community.member_count)}</td>
                <td>{formatNumber(community.post_count)}</td>
                <td className={common.dim}>{formatDate(community.created_at)}</td>
                <td>
                  <div className={common.rowActions}>
                    <ButtonLink to={`/moderation/communautes/${community.slug}`} size="sm" variant="secondary">
                      Modifier
                    </ButtonLink>
                    <ButtonLink to={`/communautes/${community.slug}`} size="sm" variant="secondary">
                      Membres
                    </ButtonLink>
                    <Button size="sm" variant="danger" onClick={() => void remove(community)}>
                      Supprimer
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!communities.loading && shown.length === 0 && <p className={common.empty}>Aucune communauté.</p>}
      </div>
    </div>
  )
}
