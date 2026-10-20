import { ArrowLeft, Check, Lock, Plus } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router'
import { outingsApi } from '../../api/outings'
import { friendsApi, usersApi, type Profile, type Relation } from '../../api/users'
import { useAuth } from '../../auth/context'
import { Button, ButtonLink, Card, Notice, OutingCard, PostTile, ReportDialog, Tag } from '../../components'
import { ApiError } from '../../lib/api'
import { formatCount, formatMonthYear, formatOutingDate } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import styles from './profile.module.css'
import { ProfileHeader } from './ProfileHeader'

function firstName(profile: Profile): string {
  return profile.user.display_name.split(' ')[0]
}

/** Écrans 06 et 06b · Profil d'un autre utilisateur, selon la relation d'amitié. */
export function UserProfilePage() {
  const { username = '' } = useParams()
  return <UserProfile key={username} username={username} />
}

function UserProfile({ username }: { username: string }) {
  const navigate = useNavigate()
  const profile = useApi(`profile:${username}`, () => usersApi.profile(username), 'Ce profil n’a pas pu être chargé.')
  const posts = useApi(`posts:${username}`, () => usersApi.posts(username), 'Les publications n’ont pas pu être chargées.')
  const outings = useApi(`outings:${username}`, () => usersApi.outings(username), 'Les sorties n’ont pas pu être chargées.')
  const { me } = useAuth()
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [reporting, setReporting] = useState(false)

  if (profile.errorCode === 'not_found') {
    return (
      <div className={styles.page}>
        <Notice tone="danger">Cet utilisateur n’existe pas.</Notice>
      </div>
    )
  }
  if (!profile.data) return profile.error ? <Notice tone="danger">{profile.error}</Notice> : null
  const data = profile.data
  if (data.relation === 'self') return <Navigate to="/profil" replace />

  const name = firstName(data)
  const items = posts.data?.items ?? []
  const isFriend = data.relation === 'friends'

  /** Change la relation, puis recharge profil et posts (compteurs et posts visibles changent). */
  async function act(action: () => Promise<{ relation: Relation }>, confirmMessage?: string) {
    if (confirmMessage && !window.confirm(confirmMessage)) return
    setBusy(true)
    setActionError(null)
    try {
      await action()
      profile.reload()
      posts.reload()
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'L’action n’a pas pu aboutir.')
    } finally {
      setBusy(false)
    }
  }

  const invite = <InviteMenu username={username} name={name} primary={isFriend} />

  let actions
  switch (data.relation) {
    case 'friends':
      actions = (
        <>
          <Button
            variant="secondary"
            className={styles.iconAfter}
            icon={<Check aria-hidden size={16} />}
            disabled={busy}
            title="Retirer des amis"
            onClick={() => void act(() => friendsApi.remove(username), `Retirer ${data.user.display_name} de vos amis ?`)}
          >
            Amis
          </Button>
          {invite}
        </>
      )
      break
    case 'request_sent':
      actions = (
        <>
          <Button
            variant="secondary"
            disabled={busy}
            title="Annuler la demande"
            onClick={() => void act(() => friendsApi.cancel(username), 'Annuler votre demande d’ami ?')}
          >
            Demande envoyée
          </Button>
          {invite}
        </>
      )
      break
    case 'request_received':
      actions = (
        <>
          <Button disabled={busy} onClick={() => void act(() => friendsApi.accept(username))}>
            Accepter la demande
          </Button>
          <Button variant="secondary" disabled={busy} onClick={() => void act(() => friendsApi.decline(username))}>
            Refuser
          </Button>
        </>
      )
      break
    default:
      actions = (
        <>
          <Button
            icon={<Plus aria-hidden size={16} />}
            disabled={busy || !data.can_send_request}
            title={data.can_send_request ? undefined : `${name} n’accepte que les membres de ses communautés.`}
            onClick={() => void act(() => friendsApi.request(username))}
          >
            Ajouter en ami
          </Button>
          {invite}
        </>
      )
  }

  const meta = isFriend && data.friends_since ? `Ami depuis ${formatMonthYear(data.friends_since)}` : `membre depuis ${new Date(data.member_since).getFullYear()}`
  const hasPrivatePosts = items.some((post) => post.visibility === 'friends')

  return (
    <div className={styles.page}>
      <button type="button" className={styles.back} onClick={() => navigate(-1)}>
        <ArrowLeft aria-hidden size={14} />
        Retour
      </button>

      <ProfileHeader
        profile={data}
        meta={meta}
        actions={
          <>
            {actions}
            <button type="button" className={`${styles.textAction} ${styles.danger}`} onClick={() => setReporting(true)}>
              Signaler ce profil
            </button>
          </>
        }
      />
      {reporting && (
        <ReportDialog target={{ username }} label={`le profil de ${data.user.display_name}`} onClose={() => setReporting(false)} />
      )}
      {actionError && <Notice tone="danger">{actionError}</Notice>}

      <div className={styles.columns}>
        <div className={styles.column}>
          <h2 className={styles.sectionTitle}>Ses sorties à venir</h2>
          {outings.data?.items.map((outing) => (
            <OutingCard key={outing.id} outing={outing} viewerUsername={me?.user.username} compact />
          ))}
          {outings.data && outings.data.items.length === 0 && (
            <Card padding="compact">
              <p className={styles.muted}>
                {outings.data.hidden ? `${name} ne partage pas ses sorties à venir.` : 'Aucune sortie à venir.'}
              </p>
            </Card>
          )}
        </div>

        <aside className={styles.aside}>
          {data.communities.length > 0 && (
            <Card title="Communautés en commun">
              <div className={styles.tags}>
                {data.communities.map((community) => (
                  <Link key={community.slug} to={`/communautes/${community.slug}`} className={styles.tagLink}>
                    <Tag>{community.name}</Tag>
                  </Link>
                ))}
              </div>
            </Card>
          )}

          <Card title="Publications">
            {posts.error && <Notice tone="danger">{posts.error}</Notice>}
            {items.length > 0 && (
              <div className={styles.tiles}>
                {items.map((post) => (
                  // Badge seulement sur les posts « Amis », que seuls les amis voient (écran 06b).
                  <PostTile key={post.id} post={post} showBadge={post.visibility === 'friends'} />
                ))}
              </div>
            )}
            {data.hidden_post_count > 0 && (
              <div className={styles.locked}>
                <Lock aria-hidden size={22} />
                <span className={styles.lockedTitle}>
                  {formatCount(data.hidden_post_count, 'publication réservée', 'publications réservées')} aux amis
                </span>
                <span>Ajoutez {name} en ami pour les voir.</span>
              </div>
            )}
            {hasPrivatePosts && (
              <p className={styles.legend}>
                <Lock aria-hidden size={14} />
                Visible uniquement par les amis de {name}
              </p>
            )}
            {!posts.loading && items.length === 0 && data.hidden_post_count === 0 && (
              <p className={styles.muted}>Aucune publication.</p>
            )}
          </Card>
        </aside>
      </div>
    </div>
  )
}

/** « Inviter à une sortie » : choisit une de mes sorties à venir et y invite la personne. */
function InviteMenu({ username, name, primary }: { username: string; name: string; primary: boolean }) {
  const [open, setOpen] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const ref = useRef<HTMLDivElement>(null)
  const mine = useApi(`outings:mine`, () => outingsApi.list('mine'), 'Vos sorties n’ont pas pu être chargées.')

  useEffect(() => {
    if (!open) return
    function close(event: MouseEvent) {
      if (!ref.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [open])

  async function invite(outingId: number, title: string) {
    setOpen(false)
    try {
      await outingsApi.invite(outingId, username)
      setMessage(`Invitation envoyée à ${name} pour « ${title} ».`)
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : 'L’invitation n’a pas pu être envoyée.')
    }
  }

  return (
    <div className={styles.inviteMenu} ref={ref}>
      <Button variant={primary ? 'primary' : 'secondary'} fullWidth aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((value) => !value)}>
        Inviter à une sortie
      </Button>
      {open && (
        <div className={styles.menuList} role="menu">
          {mine.data?.length === 0 && (
            <div className={styles.menuEmpty}>
              <span>Vous n’organisez aucune sortie à venir.</span>
              <ButtonLink to="/sorties/nouvelle" size="sm">
                Créer une sortie
              </ButtonLink>
            </div>
          )}
          {mine.data?.map((outing) => (
            <button key={outing.id} type="button" role="menuitem" className={styles.menuItem} onClick={() => void invite(outing.id, outing.title)}>
              <span className={styles.menuTitle}>{outing.title}</span>
              <span className={styles.menuMeta}>{formatOutingDate(outing.starts_at)}</span>
            </button>
          ))}
        </div>
      )}
      {message && (
        <p className={styles.menuMessage} role="status">
          {message}
        </p>
      )}
    </div>
  )
}
