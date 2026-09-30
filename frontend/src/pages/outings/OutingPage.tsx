import { ArrowLeft, Check, Link2, Pencil } from 'lucide-react'
import { lazy, Suspense, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { outingsApi, type OutingDetail } from '../../api/outings'
import { friendsApi } from '../../api/users'
import { AvatarGroup, Button, ButtonLink, Card, Notice, StatusBadge, StopNumber, UserRow } from '../../components'
import { ApiError } from '../../lib/api'
import { formatAltitude, formatDistance, formatNumber, formatOutingDate, shortName } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import styles from './OutingPage.module.css'

// Leaflet n'est chargé qu'en ouvrant une sortie.
const OutingMap = lazy(async () => ({ default: (await import('./OutingMap')).OutingMap }))

const VISIBILITY_LABELS = { public: 'Publique', invitation: 'Sur invitation' }

function InfoRow({ label, value, title }: { label: string; value: string; title?: string }) {
  return (
    <div className={styles.infoRow}>
      <dt>{label}</dt>
      <dd title={title}>{value}</dd>
    </div>
  )
}

/** Écran 11 · Détail d'une sortie. */
export function OutingPage() {
  const { id = '' } = useParams()
  return <OutingView key={id} id={Number(id)} />
}

function OutingView({ id }: { id: number }) {
  const outing = useApi(`outing:${id}`, () => outingsApi.get(id), 'La sortie n’a pas pu être chargée.')
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!copied) return
    const timer = window.setTimeout(() => setCopied(false), 2000)
    return () => window.clearTimeout(timer)
  }, [copied])

  if (outing.errorCode === 'not_found' || !Number.isInteger(id)) {
    return (
      <div className={styles.page}>
        <Notice tone="danger">Cette sortie n’existe pas ou vous n’y êtes pas invité.</Notice>
        <Link to="/sorties" className={styles.back}>
          ← Toutes les sorties
        </Link>
      </div>
    )
  }
  if (!outing.data) return outing.error ? <Notice tone="danger">{outing.error}</Notice> : null
  const data = outing.data
  const past = new Date(data.starts_at) < new Date()

  async function act(action: () => Promise<OutingDetail>) {
    setBusy(true)
    setActionError(null)
    try {
      outing.setData(await action())
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'L’action n’a pas pu aboutir.')
    } finally {
      setBusy(false)
    }
  }

  async function share() {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopied(true)
    } catch {
      setActionError('Copiez l’adresse de la page pour partager la sortie.')
    }
  }

  let mainAction
  if (data.is_organizer) {
    mainAction = past ? null : (
      <ButtonLink to={`/sorties/${data.id}/modifier`} icon={<Pencil aria-hidden size={16} />} className={styles.grow}>
        Modifier la sortie
      </ButtonLink>
    )
  } else if (data.is_participant) {
    mainAction = past ? null : (
      <Button variant="secondary" className={styles.grow} disabled={busy} onClick={() => void act(() => outingsApi.leave(data.id))}>
        Quitter la sortie
      </Button>
    )
  } else {
    let label = 'Rejoindre la sortie'
    if (past) label = 'Sortie passée'
    else if (data.status === 'full') label = 'Sortie complète'
    mainAction = (
      <Button className={styles.grow} disabled={busy || !data.can_join} onClick={() => void act(() => outingsApi.join(data.id))}>
        {label}
      </Button>
    )
  }

  const distance = [formatDistance(data.distance_m)]
  if (data.elevation_gain_m) distance.push(`+${formatNumber(data.elevation_gain_m)} m`)

  return (
    <div className={styles.page}>
      <Link to="/sorties" className={styles.back}>
        <ArrowLeft aria-hidden size={14} />
        Sorties
      </Link>

      <div className={styles.columns}>
        <div className={styles.mapBox}>
          <Suspense fallback={null}>
            <OutingMap stops={data.stops} path={data.path} fitKey={String(data.id)} />
          </Suspense>
        </div>

        <aside className={styles.aside}>
          <Card>
            <div className={styles.titleRow}>
              <h1 className={styles.title}>{data.title}</h1>
              {data.status === 'full' ? (
                <StatusBadge tone="accent">Complète</StatusBadge>
              ) : (
                <StatusBadge tone="success">Ouverte</StatusBadge>
              )}
            </div>
            <dl className={styles.info}>
              <InfoRow label="Date" value={formatOutingDate(data.starts_at)} />
              <InfoRow label="Organisation" value={shortName(data.organizer.display_name)} />
              <InfoRow
                label="Distance"
                value={distance.join(' · ')}
                title={
                  data.path.length >= 2
                    ? 'Longueur du chemin tracé. Dénivelé approximatif, calculé entre les refuges.'
                    : 'À vol d’oiseau entre les points de stop. Dénivelé approximatif, calculé entre les refuges.'
                }
              />
              <InfoRow label="Visibilité" value={VISIBILITY_LABELS[data.visibility]} />
            </dl>
          </Card>

          <Card title="Points de stop">
            <ol className={styles.stops}>
              {data.stops.map((stop) => (
                <li key={stop.position} className={styles.stop}>
                  <StopNumber value={stop.position} />
                  <div className={styles.stopText}>
                    {stop.refuge_id ? (
                      <Link to={`/refuges/${stop.refuge_id}`} className={styles.stopName}>
                        {stop.name}
                      </Link>
                    ) : (
                      <span className={styles.stopName}>{stop.name}</span>
                    )}
                    <span className={styles.stopMeta}>
                      {stop.altitude ? formatAltitude(stop.altitude) : stop.refuge_id ? 'Refuge' : 'Point libre'}
                      {stop.position === 1 && ' · départ'}
                    </span>
                  </div>
                </li>
              ))}
            </ol>
          </Card>

          <Card
            title="Participants"
            action={
              <span className={styles.count}>
                {data.participant_count} / {data.max_participants}
              </span>
            }
          >
            <AvatarGroup size="lg" max={12} names={data.participants.map((p) => p.display_name)} />
            <p className={styles.names}>
              {data.participants.map((p, index) => (
                <span key={p.username}>
                  {index > 0 && ', '}
                  <Link to={`/u/${p.username}`}>{shortName(p.display_name)}</Link>
                </span>
              ))}
            </p>
          </Card>

          {actionError && <Notice tone="danger">{actionError}</Notice>}
          <div className={styles.actions}>
            {mainAction}
            <Button variant="secondary" icon={copied ? <Check aria-hidden size={16} /> : <Link2 aria-hidden size={16} />} onClick={() => void share()}>
              {copied ? 'Lien copié' : 'Partager'}
            </Button>
          </div>

          {data.is_organizer && data.visibility === 'invitation' && !past && <InviteFriends outing={data} />}
        </aside>
      </div>
    </div>
  )
}

/** Sortie « Sur invitation » : l'organisateur invite ses amis (pas d'écran dédié dans la maquette). */
function InviteFriends({ outing }: { outing: OutingDetail }) {
  const friends = useApi('friends', friendsApi.list, 'Vos amis n’ont pas pu être chargés.')
  const [invited, setInvited] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const participants = new Set(outing.participants.map((p) => p.username))
  const candidates = (friends.data?.friends ?? []).filter((f) => !participants.has(f.user.username))

  async function invite(username: string) {
    setError(null)
    try {
      await outingsApi.invite(outing.id, username)
      setInvited((list) => [...list, username])
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'L’invitation n’a pas pu être envoyée.')
    }
  }

  return (
    <Card title="Inviter des amis">
      <p className={styles.stopMeta}>Seules les personnes invitées voient cette sortie et peuvent la rejoindre.</p>
      {error && <Notice tone="danger">{error}</Notice>}
      {!friends.loading && candidates.length === 0 && <p className={styles.stopMeta}>Aucun ami à inviter.</p>}
      {candidates.map((friend) => (
        <UserRow
          key={friend.user.username}
          name={friend.user.display_name}
          username={friend.user.username}
          actions={
            invited.includes(friend.user.username) ? (
              <StatusBadge tone="success" icon={<Check aria-hidden size={14} />}>
                Invité
              </StatusBadge>
            ) : (
              <Button size="sm" variant="secondary" onClick={() => void invite(friend.user.username)}>
                Inviter
              </Button>
            )
          }
        />
      ))}
    </Card>
  )
}
