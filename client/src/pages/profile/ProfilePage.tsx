import { Lock, Plus } from 'lucide-react'
import { Link } from 'react-router'
import { usersApi, type Profile } from '../../api/users'
import { useAuth } from '../../auth/context'
import { AvatarGroup, ButtonLink, Card, Notice, OutingCard, PostTile, StatusBadge, Tag } from '../../components'
import { formatCount } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import styles from './profile.module.css'
import { ProfileHeader } from './ProfileHeader'

const NAMED_FRIENDS = 3

/** « Lucas, Sarah, Antoine et 83 autres ». */
function friendNames(profile: Profile): string {
  const preview = profile.friends_preview ?? []
  const names = preview.slice(0, NAMED_FRIENDS).map((friend) => friend.display_name.split(' ')[0])
  const others = (profile.friend_count ?? preview.length) - names.length
  if (others <= 0) return names.join(', ').replace(/, ([^,]*)$/, ' et $1')
  return `${names.join(', ')} et ${formatCount(others, 'autre')}`
}

/** Écran 05 · Mon profil. */
export function ProfilePage() {
  const { me, logout } = useAuth()
  const username = me?.user.username ?? ''
  const profile = useApi(`profile:${username}`, () => usersApi.profile(username), 'Votre profil n’a pas pu être chargé.')
  const outings = useApi(`outings:${username}`, () => usersApi.outings(username), 'Vos sorties n’ont pas pu être chargées.')
  const posts = useApi(`posts:${username}`, () => usersApi.posts(username), 'Vos publications n’ont pas pu être chargées.')

  if (!profile.data) return profile.error ? <Notice tone="danger">{profile.error}</Notice> : null
  const data = profile.data
  const pending = data.pending_request_count ?? 0
  const items = posts.data?.items ?? []

  return (
    <div className={styles.page}>
      <ProfileHeader
        profile={data}
        meta={`membre depuis ${new Date(data.member_since).getFullYear()}`}
        actions={
          <>
            <ButtonLink to="/profil/modifier" variant="secondary">
              Modifier le profil
            </ButtonLink>
            <Link to="/parametres/confidentialite" className={styles.textAction}>
              Confidentialité
            </Link>
            <button type="button" className={`${styles.textAction} ${styles.danger}`} onClick={() => void logout()}>
              Se déconnecter
            </button>
          </>
        }
      />

      <div className={styles.columns}>
        <div className={styles.column}>
          <h2 className={styles.sectionTitle}>Mes sorties à venir</h2>
          {outings.error && <Notice tone="danger">{outings.error}</Notice>}
          {outings.data?.items.map((outing) => (
            <OutingCard key={outing.id} outing={outing} viewerUsername={username} compact />
          ))}
          {outings.data?.items.length === 0 && (
            <Card padding="compact">
              <div className={styles.friendsSummary}>
                <p className={`${styles.muted} ${styles.friendsCount}`}>Aucune sortie à venir.</p>
                <ButtonLink to="/sorties" size="sm" variant="secondary">
                  Voir les sorties
                </ButtonLink>
              </div>
            </Card>
          )}

          <h2 className={styles.sectionTitle}>Mes amis</h2>
          <Card padding="compact">
            <div className={styles.friendsSummary}>
              {pending > 0 && (
                <StatusBadge tone="pending">
                  {pending} demande{pending > 1 ? 's' : ''} d’ami en attente
                </StatusBadge>
              )}
              <span className={styles.friendsCount}>{formatCount(data.friend_count ?? 0, 'ami')}</span>
              <Link to="/profil/amis" className={styles.link}>
                Gérer mes amis →
              </Link>
            </div>
            {data.friends_preview && data.friends_preview.length > 0 ? (
              <div className={styles.friendsPreview}>
                <AvatarGroup size="xl" max={8} names={data.friends_preview.map((friend) => friend.display_name)} />
                <span>{friendNames(data)}</span>
              </div>
            ) : (
              <p className={styles.muted}>Ajoutez des amis depuis leur profil ou les suggestions.</p>
            )}
          </Card>
        </div>

        <aside className={styles.aside}>
          <Card title="Mes communautés">
            {data.communities.length > 0 ? (
              <div className={styles.tags}>
                {data.communities.map((community) => (
                  <Link key={community.slug} to={`/communautes/${community.slug}`} className={styles.tagLink}>
                    <Tag>{community.name}</Tag>
                  </Link>
                ))}
              </div>
            ) : (
              <p className={styles.muted}>
                Vous n’avez rejoint aucune communauté. <Link to="/communautes" className={styles.link}>Découvrir</Link>
              </p>
            )}
          </Card>

          <Card
            title="Mes publications"
            action={
              <Link to="/posts/nouveau" className={styles.link}>
                <Plus aria-hidden size={14} /> Publier
              </Link>
            }
          >
            {posts.error && <Notice tone="danger">{posts.error}</Notice>}
            {items.length > 0 ? (
              <>
                <div className={styles.tiles}>
                  {items.map((post) => (
                    <PostTile key={post.id} post={post} />
                  ))}
                </div>
                <p className={styles.legend}>
                  <Lock aria-hidden size={14} />
                  Amis : visible seulement par vos amis · Public : visible par tous
                </p>
              </>
            ) : (
              !posts.loading && <p className={styles.muted}>Vous n’avez encore rien publié.</p>
            )}
          </Card>
        </aside>
      </div>
    </div>
  )
}
