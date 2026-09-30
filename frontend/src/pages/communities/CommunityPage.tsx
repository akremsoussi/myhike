import { ArrowLeft, Check, ChevronRight } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { communitiesApi, postsApi, type Community, type Post } from '../../api/communities'
import { useAuth } from '../../auth/context'
import { Avatar, AvatarGroup, Button, ButtonLink, Card, Notice, PostCard, ReportDialog } from '../../components'
import { ApiError } from '../../lib/api'
import { formatCount, formatNumber } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import styles from './CommunityPage.module.css'

const MEMBERS_SHOWN = 6

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback
}

/** Fil de la communauté, page par page (« Voir plus »). */
function useFeed(slug: string) {
  const [posts, setPosts] = useState<Post[]>([])
  const [nextBefore, setNextBefore] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    communitiesApi
      .posts(slug)
      .then((page) => {
        if (cancelled) return
        setPosts(page.items)
        setNextBefore(page.next_before)
        setError(null)
      })
      .catch((err: unknown) => !cancelled && setError(errorMessage(err, 'Les posts n’ont pas pu être chargés.')))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [slug])

  async function loadMore() {
    if (nextBefore === null) return
    setLoading(true)
    try {
      const page = await communitiesApi.posts(slug, nextBefore)
      setPosts((current) => [...current, ...page.items])
      setNextBefore(page.next_before)
    } catch (err) {
      setError(errorMessage(err, 'Les posts n’ont pas pu être chargés.'))
    } finally {
      setLoading(false)
    }
  }

  return { posts, setPosts, hasMore: nextBefore !== null, loading, error, setError, loadMore }
}

/** Écran 08 · Page communauté. Remontée à chaque changement de communauté (état remis à zéro). */
export function CommunityPage() {
  const { slug = '' } = useParams()
  return <CommunityView key={slug} slug={slug} />
}

function CommunityView({ slug }: { slug: string }) {
  const { me } = useAuth()
  const detail = useApi(`community:${slug}`, () => communitiesApi.get(slug), 'La communauté n’a pas pu être chargée.')
  const feed = useFeed(slug)
  const [busy, setBusy] = useState<string | null>(null)
  const [reporting, setReporting] = useState<Post | null>(null)

  const community = detail.data

  if (detail.errorCode === 'not_found') {
    return (
      <div className={styles.content}>
        <Notice tone="danger">Cette communauté n’existe pas.</Notice>
        <Link to="/communautes" className={styles.inlineLink}>
          ← Toutes les communautés
        </Link>
      </div>
    )
  }
  if (!community || !me) {
    return <div className={styles.content}>{detail.error && <Notice tone="danger">{detail.error}</Notice>}</div>
  }

  async function run(key: string, action: () => Promise<void>, fallback: string) {
    setBusy(key)
    feed.setError(null)
    try {
      await action()
    } catch (err) {
      feed.setError(errorMessage(err, fallback))
    } finally {
      setBusy(null)
    }
  }

  function toggleMembership() {
    void run(
      'membership',
      async () => {
        const updated: Community = isMember
          ? await communitiesApi.leave(slug)
          : await communitiesApi.join(slug)
        detail.setData((current) => current && { ...current, ...updated })
      },
      'L’action n’a pas pu aboutir.',
    )
  }

  function toggleLike(post: Post) {
    void run(
      `post:${post.id}`,
      async () => {
        const likes = post.liked ? await postsApi.unlike(post.id) : await postsApi.like(post.id)
        feed.setPosts((posts) => posts.map((item) => (item.id === post.id ? { ...item, ...likes } : item)))
      },
      'Le j’aime n’a pas pu être enregistré.',
    )
  }

  function remove(post: Post) {
    if (!window.confirm('Supprimer ce post ? Cette action est définitive.')) return
    void run(
      `post:${post.id}`,
      async () => {
        await postsApi.remove(post.id)
        feed.setPosts((posts) => posts.filter((item) => item.id !== post.id))
        detail.setData((current) => current && { ...current, post_count: current.post_count - 1 })
      },
      'Le post n’a pas pu être supprimé.',
    )
  }

  const isMember = community.is_member
  const newPostUrl = `/posts/nouveau?communaute=${encodeURIComponent(slug)}`
  const hiddenMembers = community.member_count - Math.min(community.members.length, MEMBERS_SHOWN)

  return (
    <>
      <section className={styles.banner}>
        <div className={styles.bannerInner}>
          <div className={styles.bannerText}>
            <Link to="/communautes" className={styles.back}>
              <ArrowLeft aria-hidden size={14} />
              Communautés
            </Link>
            <h1 className={styles.name}>{community.name}</h1>
            <p className={styles.bannerMeta}>
              {formatCount(community.member_count, 'membre')} · {formatCount(community.post_count, 'post')} ·{' '}
              {community.massif?.name ?? community.region}
            </p>
          </div>
          {community.is_member ? (
            <Button
              variant="secondary"
              className={styles.joined}
              icon={<Check aria-hidden size={16} />}
              disabled={busy === 'membership'}
              onClick={toggleMembership}
              title="Quitter la communauté"
            >
              Inscrit
            </Button>
          ) : (
            <Button className={styles.join} disabled={busy === 'membership'} onClick={toggleMembership}>
              Rejoindre
            </Button>
          )}
        </div>
      </section>

      <div className={styles.content}>
        <div className={styles.columns}>
          <div className={styles.feed}>
            {community.is_member ? (
              <div className={styles.composer}>
                <Avatar name={me.user.display_name} size="2xl" />
                <Link to={newPostUrl} className={styles.composerInput}>
                  Partager une photo ou un chemin…
                </Link>
                <ButtonLink to={newPostUrl}>Nouveau post</ButtonLink>
              </div>
            ) : (
              <Notice>Rejoignez la communauté pour y publier.</Notice>
            )}

            {feed.error && <Notice tone="danger">{feed.error}</Notice>}

            {feed.posts.map((post) => (
              <PostCard
                key={post.id}
                post={{ ...post, community: null }}
                busy={busy === `post:${post.id}`}
                onToggleLike={() => toggleLike(post)}
                onDelete={() => remove(post)}
                onReport={post.author.username === me.user.username ? undefined : () => setReporting(post)}
              />
            ))}

            {reporting && (
              <ReportDialog
                target={{ post_id: reporting.id }}
                label={`le post de ${reporting.author.display_name}`}
                onClose={() => setReporting(null)}
              />
            )}
            {!feed.loading && feed.posts.length === 0 && !feed.error && (
              <p className={styles.empty}>Aucun post pour l’instant.</p>
            )}
            {feed.hasMore && (
              <Button variant="secondary" disabled={feed.loading} onClick={() => void feed.loadMore()}>
                {feed.loading ? 'Chargement…' : 'Voir plus'}
              </Button>
            )}
          </div>

          <aside className={styles.aside}>
            <Card title="À propos">
              <p className={styles.about}>{community.description || 'Pas encore de description.'}</p>
            </Card>

            <Card title="Membres">
              {community.members.length > 0 ? (
                <div className={styles.members}>
                  <AvatarGroup
                    size="xl"
                    max={MEMBERS_SHOWN}
                    names={community.members.map((member) => member.display_name)}
                  />
                  {hiddenMembers > 0 && <span className={styles.moreMembers}>+{formatNumber(hiddenMembers)}</span>}
                </div>
              ) : (
                <p className={styles.about}>Aucun membre pour l’instant.</p>
              )}
            </Card>

            {community.refuges.length > 0 && (
              <Card title="Refuges de la communauté">
                <ul className={styles.refuges}>
                  {community.refuges.map((refuge) => (
                    <li key={refuge.id}>
                      <Link to={`/refuges/${refuge.id}`} className={styles.refuge}>
                        {refuge.name}
                        <ChevronRight aria-hidden size={16} className={styles.chevron} />
                      </Link>
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {community.is_member && (
              <Button variant="danger" fullWidth disabled={busy === 'membership'} onClick={toggleMembership}>
                Quitter la communauté
              </Button>
            )}
          </aside>
        </div>
      </div>
    </>
  )
}
