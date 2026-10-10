import { useEffect, useState } from 'react'
import { postsApi, type Post, type PostPage } from '../../api/communities'
import { useAuth } from '../../auth/context'
import { Button, Notice, PostCard, ReportDialog } from '../../components'
import { ApiError } from '../../lib/api'
import styles from './PostFeed.module.css'

type PostFeedProps = {
  /** Page de posts avant l'identifiant `before` (la première si absent). */
  load: (before?: number) => Promise<PostPage>
  /** Fil d'une communauté : inutile de rappeler la communauté sur chaque post. */
  hideCommunity?: boolean
  /** Posts liés à un refuge : inutile de rappeler le refuge. */
  hideRefuge?: boolean
  empty: string
  /** Post supprimé (pour mettre à jour un compteur). */
  onDeleted?: (post: Post) => void
}

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback
}

/**
 * Fil de posts page par page (« Voir plus ») avec j'aime, suppression et signalement.
 * À remonter (`key`) quand la source change : l'état repart de zéro.
 */
export function PostFeed({ load, hideCommunity = false, hideRefuge = false, empty, onDeleted }: PostFeedProps) {
  const { me } = useAuth()
  const [posts, setPosts] = useState<Post[]>([])
  const [nextBefore, setNextBefore] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<number | null>(null)
  const [reporting, setReporting] = useState<Post | null>(null)

  useEffect(() => {
    let cancelled = false
    load()
      .then((page) => {
        if (cancelled) return
        setPosts(page.items)
        setNextBefore(page.next_before)
      })
      .catch((err: unknown) => !cancelled && setError(errorMessage(err, 'Les posts n’ont pas pu être chargés.')))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
    // Chargé au montage seulement : la page parente remonte le fil quand la source change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function loadMore() {
    if (nextBefore === null) return
    setLoading(true)
    try {
      const page = await load(nextBefore)
      setPosts((current) => [...current, ...page.items])
      setNextBefore(page.next_before)
    } catch (err) {
      setError(errorMessage(err, 'Les posts n’ont pas pu être chargés.'))
    } finally {
      setLoading(false)
    }
  }

  async function run(post: Post, action: () => Promise<void>, fallback: string) {
    setBusy(post.id)
    setError(null)
    try {
      await action()
    } catch (err) {
      setError(errorMessage(err, fallback))
    } finally {
      setBusy(null)
    }
  }

  function toggleLike(post: Post) {
    void run(
      post,
      async () => {
        const likes = post.liked ? await postsApi.unlike(post.id) : await postsApi.like(post.id)
        setPosts((list) => list.map((item) => (item.id === post.id ? { ...item, ...likes } : item)))
      },
      'Le j’aime n’a pas pu être enregistré.',
    )
  }

  function remove(post: Post) {
    if (!window.confirm('Supprimer ce post ? Cette action est définitive.')) return
    void run(
      post,
      async () => {
        await postsApi.remove(post.id)
        setPosts((list) => list.filter((item) => item.id !== post.id))
        onDeleted?.(post)
      },
      'Le post n’a pas pu être supprimé.',
    )
  }

  return (
    <div className={styles.feed}>
      {error && <Notice tone="danger">{error}</Notice>}
      {posts.map((post) => (
        <PostCard
          key={post.id}
          post={{ ...post, community: hideCommunity ? null : post.community, refuge: hideRefuge ? null : post.refuge }}
          busy={busy === post.id}
          onToggleLike={() => toggleLike(post)}
          onDelete={() => remove(post)}
          onReport={post.author.username === me?.user.username ? undefined : () => setReporting(post)}
        />
      ))}
      {reporting && (
        <ReportDialog
          target={{ post_id: reporting.id }}
          label={`le post de ${reporting.author.display_name}`}
          onClose={() => setReporting(null)}
        />
      )}
      {!loading && posts.length === 0 && !error && <p className={styles.empty}>{empty}</p>}
      {nextBefore !== null && (
        <Button variant="secondary" disabled={loading} onClick={() => void loadMore()}>
          {loading ? 'Chargement…' : 'Voir plus'}
        </Button>
      )}
    </div>
  )
}
