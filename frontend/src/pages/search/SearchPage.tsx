import { ChevronRight } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link, useSearchParams } from 'react-router'
import { useAuth } from '../../auth/context'
import { searchApi, SEARCH_MIN_LENGTH } from '../../api/search'
import { Card, CommunityCard, Notice, OutingCard, Tag, UserRow } from '../../components'
import { useApi } from '../../lib/useApi'
import { altitudeAndCapacity, guardLabel, isClosed } from '../map/refugeText'
import { PostFeed } from '../posts/PostFeed'
import styles from './SearchPage.module.css'

function Section({ title, count, children }: { title: string; count: number; children: ReactNode }) {
  if (count === 0) return null
  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>
        {title} <span className={styles.count}>{count}</span>
      </h2>
      {children}
    </section>
  )
}

/** Résultats de la recherche de la barre de navigation (/recherche?q=…). */
export function SearchPage() {
  const [params] = useSearchParams()
  const q = (params.get('q') ?? '').trim()
  if (q.length < SEARCH_MIN_LENGTH) {
    return (
      <div className={styles.page}>
        <h1 className={styles.title}>Recherche</h1>
        <p className={styles.muted}>Tapez au moins {SEARCH_MIN_LENGTH} caractères dans la barre de recherche.</p>
      </div>
    )
  }
  return <Results key={q} q={q} />
}

function Results({ q }: { q: string }) {
  const { me } = useAuth()
  const { data, error, loading } = useApi(`search:${q}`, () => searchApi.search(q), 'La recherche n’a pas abouti.')
  const total = data
    ? data.refuges.length + data.communities.length + data.users.length + data.outings.length + data.posts.length
    : 0

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Résultats pour « {q} »</h1>
      {error && <Notice tone="danger">{error}</Notice>}
      {loading && <p className={styles.muted}>Recherche…</p>}
      {data && total === 0 && (
        <p className={styles.muted}>Aucun résultat. Essayez un nom de refuge, de massif, de communauté ou de randonneur.</p>
      )}
      {data && (
        <>
          <Section title="Refuges" count={data.refuges.length}>
            <Card padding="compact">
              <ul className={styles.list}>
                {data.refuges.map((refuge) => (
                  <li key={refuge.id}>
                    <Link to={`/refuges/${refuge.id}`} className={styles.refuge}>
                      <span className={styles.refugeName}>{refuge.name}</span>
                      <span className={styles.muted}>
                        {[refuge.massif?.name, ...altitudeAndCapacity(refuge)].filter(Boolean).join(' · ')}
                      </span>
                      <Tag tone={refuge.is_guarded && !isClosed(refuge) ? 'filled' : 'outline'}>{guardLabel(refuge)}</Tag>
                      <ChevronRight aria-hidden size={16} className={styles.chevron} />
                    </Link>
                  </li>
                ))}
              </ul>
            </Card>
          </Section>

          <Section title="Communautés" count={data.communities.length}>
            <div className={styles.grid}>
              {data.communities.map((community) => (
                <CommunityCard key={community.slug} community={community} />
              ))}
            </div>
          </Section>

          <Section title="Randonneurs" count={data.users.length}>
            <Card padding="compact">
              <ul className={styles.list}>
                {data.users.map((user) => (
                  <li key={user.id}>
                    <UserRow
                      name={user.display_name}
                      username={user.username}
                      meta={user.username === me?.user.username ? 'Vous' : undefined}
                    />
                  </li>
                ))}
              </ul>
            </Card>
          </Section>

          <Section title="Sorties à venir" count={data.outings.length}>
            <div className={styles.grid}>
              {data.outings.map((outing) => (
                <OutingCard key={outing.id} outing={outing} viewerUsername={me?.user.username} />
              ))}
            </div>
          </Section>

          <Section title="Posts" count={data.posts.length}>
            <div className={styles.posts}>
              <PostFeed load={() => Promise.resolve({ items: data.posts, next_before: null })} empty="" />
            </div>
          </Section>
        </>
      )}
    </div>
  )
}
