import { ArrowLeft, MoreHorizontal, Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'
import { friendsApi, type Friend, type FriendRequest, type Friends, type Relation } from '../../api/users'
import { Button, Card, Input, Notice, StatusBadge, Tabs, UserRow } from '../../components'
import { ApiError } from '../../lib/api'
import { formatCount, formatDay, formatNumber, formatRelative } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import styles from './FriendsPage.module.css'
import profileStyles from './profile.module.css'

type Tab = 'friends' | 'received' | 'sent'

function normalize(text: string): string {
  return text.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase()
}

/** Écran 05b · Mes amis. */
export function FriendsPage() {
  const friends = useApi('friends', friendsApi.list, 'Vos amis n’ont pas pu être chargés.')
  const suggestions = useApi('suggestions', friendsApi.suggestions, 'Les suggestions n’ont pas pu être chargées.')
  const [tab, setTab] = useState<Tab>('friends')
  const [search, setSearch] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const data: Friends = friends.data ?? { friends: [], received: [], sent: [] }
  const term = normalize(search.trim())
  const matches = (item: Friend | FriendRequest) =>
    !term || normalize(`${item.user.display_name} ${item.user.username}`).includes(term)
  const shown = {
    friends: data.friends.filter(matches),
    received: data.received.filter(matches),
    sent: data.sent.filter(matches),
  }

  async function act(username: string, action: () => Promise<{ relation: Relation }>, confirmMessage?: string) {
    if (confirmMessage && !window.confirm(confirmMessage)) return
    setBusy(username)
    setActionError(null)
    try {
      await action()
      friends.reload()
      suggestions.reload()
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'L’action n’a pas pu aboutir.')
    } finally {
      setBusy(null)
    }
  }

  const receivedCard = (
    <Card
      title={
        <span className={styles.titleWithCount}>
          Demandes d’ami reçues
          {data.received.length > 0 && <StatusBadge tone="pending" size="count">{data.received.length}</StatusBadge>}
        </span>
      }
    >
      {shown.received.length === 0 && <p className={profileStyles.muted}>Aucune demande en attente.</p>}
      {shown.received.map((request) => {
        const common = request.common_community_count
        const meta = [
          `@${request.user.username}`,
          common > 0 && formatCount(common, 'communauté en commun', 'communautés en commun'),
          formatRelative(request.created_at),
        ]
        return (
          <UserRow
            key={request.user.username}
            name={request.user.display_name}
            username={request.user.username}
            meta={meta.filter(Boolean).join(' · ')}
            avatarSize="3xl"
            actions={
              <>
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={busy === request.user.username}
                  onClick={() => void act(request.user.username, () => friendsApi.decline(request.user.username))}
                >
                  Refuser
                </Button>
                <Button
                  size="sm"
                  disabled={busy === request.user.username}
                  onClick={() => void act(request.user.username, () => friendsApi.accept(request.user.username))}
                >
                  Accepter
                </Button>
              </>
            }
          />
        )
      })}
    </Card>
  )

  const sentCard = (
    <Card title="Demandes envoyées">
      {shown.sent.length === 0 && <p className={profileStyles.muted}>Aucune demande envoyée.</p>}
      {shown.sent.map((request) => (
        <UserRow
          key={request.user.username}
          name={request.user.display_name}
          username={request.user.username}
          meta={`En attente · envoyée le ${formatDay(request.created_at)}`}
          actions={
            <button
              type="button"
              className={styles.cancel}
              disabled={busy === request.user.username}
              onClick={() =>
                void act(request.user.username, () => friendsApi.cancel(request.user.username), 'Annuler cette demande ?')
              }
            >
              Annuler
            </button>
          }
        />
      ))}
    </Card>
  )

  return (
    <div className={profileStyles.page}>
      <Link to="/profil" className={profileStyles.back}>
        <ArrowLeft aria-hidden size={14} />
        Mon profil
      </Link>
      <div className={styles.titleRow}>
        <h1 className={styles.title}>Mes amis</h1>
        <div className={styles.search}>
          <Input
            type="search"
            aria-label="Rechercher un ami"
            placeholder="Rechercher un ami…"
            icon={<Search aria-hidden size={16} />}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
      </div>

      <Tabs
        aria-label="Mes amis"
        value={tab}
        onChange={setTab}
        tabs={[
          { value: 'friends', label: 'Mes amis', count: data.friends.length },
          { value: 'received', label: 'Demandes reçues', count: data.received.length, countTone: 'pending' },
          { value: 'sent', label: 'Demandes envoyées', count: data.sent.length },
        ]}
      />

      {friends.error && <Notice tone="danger">{friends.error}</Notice>}
      {actionError && <Notice tone="danger">{actionError}</Notice>}

      <div className={profileStyles.columns}>
        <div className={profileStyles.column}>
          {tab === 'sent' && sentCard}
          {(tab === 'received' || (tab === 'friends' && data.received.length > 0)) && receivedCard}
          {tab === 'friends' && (
            <>
              <h2 className={styles.gridTitle}>Tous mes amis · {formatNumber(data.friends.length)}</h2>
              {!friends.loading && shown.friends.length === 0 && (
                <p className={profileStyles.muted}>
                  {term ? 'Aucun ami ne correspond à cette recherche.' : 'Vous n’avez pas encore d’amis.'}
                </p>
              )}
              <div className={styles.grid}>
                {shown.friends.map((friend) => (
                  <div key={friend.user.username} className={styles.friendCard}>
                    <UserRow
                      name={friend.user.display_name}
                      username={friend.user.username}
                      avatarSize="2xl"
                      actions={
                        <>
                          <Link to={`/u/${friend.user.username}`} className={styles.view}>
                            Voir
                          </Link>
                          <button
                            type="button"
                            className={styles.more}
                            aria-label={`Retirer ${friend.user.display_name} de vos amis`}
                            title="Retirer des amis"
                            disabled={busy === friend.user.username}
                            onClick={() =>
                              void act(
                                friend.user.username,
                                () => friendsApi.remove(friend.user.username),
                                `Retirer ${friend.user.display_name} de vos amis ?`,
                              )
                            }
                          >
                            <MoreHorizontal aria-hidden size={18} />
                          </button>
                        </>
                      }
                    />
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <aside className={profileStyles.aside}>
          {tab !== 'sent' && sentCard}
          <Card title="Suggestions">
            <p className={styles.subtitle}>Membres de vos communautés</p>
            {suggestions.data?.length === 0 && (
              <p className={profileStyles.muted}>Pas de suggestion pour l’instant. Rejoignez des communautés !</p>
            )}
            {suggestions.data?.map((suggestion) => (
              <UserRow
                key={suggestion.user.username}
                name={suggestion.user.display_name}
                username={suggestion.user.username}
                meta={[
                  suggestion.community.name,
                  suggestion.mutual_friend_count > 0 &&
                    formatCount(suggestion.mutual_friend_count, 'ami en commun', 'amis en commun'),
                ]
                  .filter(Boolean)
                  .join(' · ')}
                actions={
                  <Button
                    size="sm"
                    variant="secondary"
                    icon={<Plus aria-hidden size={14} />}
                    disabled={busy === suggestion.user.username}
                    onClick={() => void act(suggestion.user.username, () => friendsApi.request(suggestion.user.username))}
                  >
                    Ajouter
                  </Button>
                }
              />
            ))}
          </Card>
        </aside>
      </div>
    </div>
  )
}
