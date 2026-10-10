import { ArrowLeft, Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { communitiesApi, type Member } from '../../api/communities'
import { useAuth } from '../../auth/context'
import { Button, Card, Input, Notice, UserRow } from '../../components'
import { ApiError } from '../../lib/api'
import { formatCount, formatMonthYear } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import styles from './CommunityMembersPage.module.css'

const PAGE_SIZE = 50

/** « Tout voir » de la carte Membres (écran 08) : tous les membres, avec recherche. */
export function CommunityMembersPage() {
  const { slug = '' } = useParams()
  return <MembersView key={slug} slug={slug} />
}

function MembersView({ slug }: { slug: string }) {
  const { me } = useAuth()
  const community = useApi(`community:${slug}`, () => communitiesApi.get(slug), 'La communauté n’a pas pu être chargée.')
  const [search, setSearch] = useState('')
  const [members, setMembers] = useState<Member[]>([])
  const [total, setTotal] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const term = search.trim()

  // Nouvelle recherche : première page, après une courte pause de frappe.
  useEffect(() => {
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      setLoading(true)
      communitiesApi
        .members(slug, { q: term, limit: PAGE_SIZE }, controller.signal)
        .then((page) => {
          setMembers(page.items)
          setTotal(page.total)
          setError(null)
        })
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === 'AbortError') return
          setError(err instanceof ApiError ? err.message : 'Les membres n’ont pas pu être chargés.')
        })
        .finally(() => !controller.signal.aborted && setLoading(false))
    }, term ? 250 : 0)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [slug, term])

  async function loadMore() {
    setLoading(true)
    try {
      const page = await communitiesApi.members(slug, { q: term, offset: members.length, limit: PAGE_SIZE })
      setMembers((current) => [...current, ...page.items])
      setTotal(page.total)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Les membres n’ont pas pu être chargés.')
    } finally {
      setLoading(false)
    }
  }

  if (community.errorCode === 'not_found') {
    return (
      <div className={styles.page}>
        <Notice tone="danger">Cette communauté n’existe pas.</Notice>
        <Link to="/communautes" className={styles.back}>
          ← Toutes les communautés
        </Link>
      </div>
    )
  }

  const name = community.data?.name ?? ''
  return (
    <div className={styles.page}>
      <Link to={`/communautes/${encodeURIComponent(slug)}`} className={styles.back}>
        <ArrowLeft aria-hidden size={14} />
        {name || 'Communauté'}
      </Link>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Membres</h1>
          {/* Total de la liste (comptes actifs) plutôt que le compteur de la bannière. */}
          {total !== null && !term && <p className={styles.muted}>{formatCount(total, 'membre')} dans {name}</p>}
        </div>
        <div className={styles.search}>
          <Input
            type="search"
            aria-label="Rechercher un membre"
            placeholder="Rechercher un membre…"
            icon={<Search aria-hidden size={16} />}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
      </div>

      {error && <Notice tone="danger">{error}</Notice>}
      <Card>
        {members.length > 0 ? (
          <ul className={styles.list}>
            {members.map((member) => (
              <li key={member.user.id}>
                <UserRow
                  name={member.user.display_name}
                  username={member.user.username}
                  meta={
                    member.user.username === me?.user.username
                      ? `Vous · membre depuis ${formatMonthYear(member.joined_at)}`
                      : `@${member.user.username} · membre depuis ${formatMonthYear(member.joined_at)}`
                  }
                />
              </li>
            ))}
          </ul>
        ) : (
          !loading && <p className={styles.muted}>{term ? `Aucun membre ne correspond à « ${term} ».` : 'Aucun membre pour l’instant.'}</p>
        )}
      </Card>
      {total !== null && members.length < total && (
        <Button variant="secondary" disabled={loading} onClick={() => void loadMore()}>
          {loading ? 'Chargement…' : 'Voir plus'}
        </Button>
      )}
    </div>
  )
}
