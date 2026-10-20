import { ArrowLeft, Check, ChevronRight } from 'lucide-react'
import { useState, type CSSProperties } from 'react'
import { Link, useParams } from 'react-router'
import { communitiesApi, type Community } from '../../api/communities'
import { useAuth } from '../../auth/context'
import { Avatar, AvatarGroup, Button, ButtonLink, Card, Notice } from '../../components'
import { ApiError } from '../../lib/api'
import { formatCount, formatNumber } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import { PostFeed } from '../posts/PostFeed'
import styles from './CommunityPage.module.css'

const MEMBERS_SHOWN = 6

/** Écran 08 · Page communauté. Remontée à chaque changement de communauté (état remis à zéro). */
export function CommunityPage() {
  const { slug = '' } = useParams()
  return <CommunityView key={slug} slug={slug} />
}

function CommunityView({ slug }: { slug: string }) {
  const { me } = useAuth()
  const detail = useApi(`community:${slug}`, () => communitiesApi.get(slug), 'La communauté n’a pas pu être chargée.')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

  async function toggleMembership() {
    setBusy(true)
    setError(null)
    try {
      const updated: Community = isMember ? await communitiesApi.leave(slug) : await communitiesApi.join(slug)
      detail.setData((current) => current && { ...current, ...updated })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'L’action n’a pas pu aboutir.')
    } finally {
      setBusy(false)
    }
  }

  const isMember = community.is_member
  const newPostUrl = `/posts/nouveau?communaute=${encodeURIComponent(slug)}`
  const hiddenMembers = community.member_count - Math.min(community.members.length, MEMBERS_SHOWN)

  return (
    <>
      <section
        className={community.banner ? `${styles.banner} ${styles.withImage}` : styles.banner}
        style={community.banner ? ({ '--banner-image': `url(${community.banner.url})` } as CSSProperties) : undefined}
      >
        <div className={styles.bannerInner}>
          {community.icon && <img src={community.icon.url} alt="" className={styles.icon} />}
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
              disabled={busy}
              onClick={() => void toggleMembership()}
              title="Quitter la communauté"
            >
              Inscrit
            </Button>
          ) : (
            <Button className={styles.join} disabled={busy} onClick={() => void toggleMembership()}>
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

            {error && <Notice tone="danger">{error}</Notice>}

            <PostFeed
              load={(before) => communitiesApi.posts(slug, before)}
              hideCommunity
              empty="Aucun post pour l’instant."
              onDeleted={() => detail.setData((current) => current && { ...current, post_count: current.post_count - 1 })}
            />
          </div>

          <aside className={styles.aside}>
            <Card title="À propos">
              <p className={styles.about}>{community.description || 'Pas encore de description.'}</p>
            </Card>

            <Card
              title="Membres"
              action={
                <Link to={`/communautes/${encodeURIComponent(slug)}/membres`} className={styles.inlineLink}>
                  Tout voir
                </Link>
              }
            >
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
              <Button variant="danger" fullWidth disabled={busy} onClick={() => void toggleMembership()}>
                Quitter la communauté
              </Button>
            )}
          </aside>
        </div>
      </div>
    </>
  )
}
