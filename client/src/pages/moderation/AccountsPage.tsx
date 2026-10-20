import { Download, MoreHorizontal, Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import { moderationApi, type Account, type AccountDetail, type AccountFilter } from '../../api/moderation'
import { useAuth } from '../../auth/context'
import { Avatar, Button, ButtonLink, Chip, Input, Notice, StatusBadge } from '../../components'
import { ApiError } from '../../lib/api'
import { cx } from '../../lib/cx'
import { formatCount, formatDate, formatNumber } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import styles from './AccountsPage.module.css'
import common from './moderation.module.css'
import { ReportItem } from './ReportItem'

const FILTERS: { value: AccountFilter; label: string }[] = [
  { value: 'all', label: 'Tous' },
  { value: 'moderators', label: 'Modérateurs' },
  { value: 'reported', label: 'Signalés' },
  { value: 'suspended', label: 'Suspendus' },
]

/** Badge de la colonne « Rôle » : l'état le plus important l'emporte. */
function AccountBadge({ account }: { account: Account }) {
  if (account.status === 'suspended') return <StatusBadge tone="neutral" size="count">Suspendu</StatusBadge>
  if (account.open_report_count > 0) return <StatusBadge tone="danger" size="count">Signalé</StatusBadge>
  if (account.status === 'pending_email') return <StatusBadge tone="pending" size="count">En attente</StatusBadge>
  if (account.role === 'super_admin') return <StatusBadge tone="accent" size="count">Super Admin</StatusBadge>
  if (account.role === 'moderator') return <StatusBadge tone="accent" size="count">Modérateur</StatusBadge>
  return <StatusBadge tone="success" size="count">Utilisateur</StatusBadge>
}

/** Écran 16 · Gestion des comptes. `?compte=pseudo` ouvre le détail d'un compte. */
export function AccountsPage() {
  const [params, setParams] = useSearchParams()
  const selected = params.get('compte')
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<AccountFilter>('all')

  // Recherche envoyée à l'API après une courte pause de frappe.
  useEffect(() => {
    const timer = window.setTimeout(() => setQuery(search.trim()), 300)
    return () => window.clearTimeout(timer)
  }, [search])

  const accounts = useApi(`accounts:${filter}:${query}`, () => moderationApi.accounts(query, filter), 'Les comptes n’ont pas pu être chargés.')
  const data = accounts.data

  function select(username: string | null) {
    setParams(username ? { compte: username } : {}, { replace: true })
  }

  return (
    <div className={common.page}>
      <header className={common.header}>
        <div className={common.intro}>
          <h1 className={common.title}>Comptes</h1>
          <p className={common.lead}>
            {data && `${formatCount(data.total, 'compte')} · ${formatCount(data.moderator_count, 'modérateur')}`}
          </p>
        </div>
        {/* Téléchargement direct par le navigateur (même origine, le cookie suit). */}
        <ButtonLink to={moderationApi.exportUrl} reloadDocument variant="secondary" icon={<Download aria-hidden size={16} />}>
          Exporter (CSV)
        </ButtonLink>
      </header>

      <div className={common.toolbar}>
        <div className={styles.search}>
          <Input
            type="search"
            aria-label="Rechercher un compte"
            placeholder="Nom, email…"
            icon={<Search aria-hidden size={16} />}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <div className={common.toolbar} role="group" aria-label="Filtrer les comptes">
          {FILTERS.map((item) => (
            <Chip key={item.value} size="sm" selected={filter === item.value} onClick={() => setFilter(item.value)}>
              {item.label}
            </Chip>
          ))}
        </div>
      </div>

      {accounts.error && <Notice tone="danger">{accounts.error}</Notice>}

      <div className={`${common.columns} ${styles.columns}`}>
        <div className={common.tableCard}>
          <table className={common.table}>
            <thead>
              <tr>
                <th>Utilisateur</th>
                <th className={styles.role}>Rôle</th>
                <th className={styles.date}>Inscrit le</th>
                <th className={styles.more}>
                  <span className={styles.srOnly}>Détail</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((account) => (
                <tr
                  key={account.username}
                  className={cx(styles.row, selected === account.username && styles.selected)}
                  onClick={() => select(account.username)}
                >
                  <td>
                    <span className={styles.user}>
                      <Avatar name={account.display_name} size="xl" />
                      <span className={styles.identity}>
                        <span className={styles.name}>{account.display_name}</span>
                        <span className={styles.email}>{account.email}</span>
                      </span>
                    </span>
                  </td>
                  <td>
                    <AccountBadge account={account} />
                  </td>
                  <td className={common.dim}>{formatDate(account.created_at)}</td>
                  <td>
                    <button
                      type="button"
                      className={styles.moreButton}
                      aria-label={`Voir le détail de ${account.display_name}`}
                      onClick={(event) => {
                        event.stopPropagation()
                        select(account.username)
                      }}
                    >
                      <MoreHorizontal aria-hidden size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && data.items.length === 0 && <p className={common.empty}>Aucun compte ne correspond.</p>}
          {data && data.total > data.items.length && (
            <p className={common.empty}>
              {formatNumber(data.items.length)} premiers comptes sur {formatNumber(data.total)} : précisez la recherche.
            </p>
          )}
        </div>

        {selected ? (
          <AccountPanel key={selected} username={selected} onChanged={accounts.reload} onDeleted={() => select(null)} />
        ) : (
          <div className={styles.panelEmpty}>Sélectionnez un compte pour voir le détail.</div>
        )}
      </div>
    </div>
  )
}

/** Panneau de droite : chiffres, signalements et actions de modération sur un compte. */
function AccountPanel({ username, onChanged, onDeleted }: { username: string; onChanged: () => void; onDeleted: () => void }) {
  const { me } = useAuth()
  const account = useApi(`account:${username}`, () => moderationApi.account(username), 'Ce compte n’a pas pu être chargé.')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!account.data) {
    return <div className={styles.panel}>{account.error && <Notice tone="danger">{account.error}</Notice>}</div>
  }
  const data = account.data
  const isSelf = data.username === me?.user.username
  const isSuperAdmin = me?.user.role === 'super_admin'
  const targetIsSuperAdmin = data.role === 'super_admin'
  const targetIsStaff = data.role === 'moderator' || data.role === 'super_admin'
  const canChangeRole = isSuperAdmin && !isSelf && !targetIsSuperAdmin
  const canSanction = !isSelf && !targetIsSuperAdmin && (isSuperAdmin || !targetIsStaff)
  const roleDisabledTitle = isSelf
    ? 'Impossible sur votre propre compte'
    : !isSuperAdmin
      ? 'Réservé au Super Administrateur'
      : targetIsSuperAdmin
        ? 'Le rôle du Super Administrateur ne peut pas être modifié'
        : undefined
  const sanctionDisabledTitle = isSelf
    ? 'Impossible sur votre propre compte'
    : !canSanction
      ? 'Un administrateur classique ne peut pas sanctionner un autre administrateur'
      : undefined

  async function act(action: () => Promise<AccountDetail | void>, confirmMessage?: string) {
    if (confirmMessage && !window.confirm(confirmMessage)) return
    setBusy(true)
    setError(null)
    try {
      const result = await action()
      if (result) account.setData(result)
      onChanged()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'L’action n’a pas pu aboutir.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <aside className={styles.panel}>
      <Avatar name={data.display_name} size="5xl" />
      <div className={styles.panelIdentity}>
        <h2 className={styles.panelName}>{data.display_name}</h2>
        <span className={common.muted}>{data.email}</span>
      </div>
      {data.open_report_count > 0 ? (
        <StatusBadge tone="danger" size="count">
          Signalé {data.open_report_count} fois
        </StatusBadge>
      ) : (
        <AccountBadge account={data} />
      )}

      <dl className={common.facts}>
        <div>
          <dt>Inscrit le</dt>
          <dd>{formatDate(data.created_at)}</dd>
        </div>
        <div>
          <dt>Communautés</dt>
          <dd>{formatNumber(data.community_count)}</dd>
        </div>
        <div>
          <dt>Posts</dt>
          <dd>{formatNumber(data.post_count)}</dd>
        </div>
        <div>
          <dt>Sorties</dt>
          <dd>{formatNumber(data.outing_count)}</dd>
        </div>
      </dl>

      {error && <Notice tone="danger">{error}</Notice>}

      {data.reports.length > 0 && (
        <section className={styles.reports}>
          <h3 className={styles.reportsTitle}>Signalements à traiter</h3>
          {data.reports.map((report) => (
            <ReportItem
              key={report.id}
              report={report}
              compact
              onDeletePost={() =>
                void act(async () => {
                  await moderationApi.deletePost(report.post!.id)
                  account.reload()
                }, 'Supprimer ce post ?')
              }
            />
          ))}
          <Button variant="secondary" fullWidth disabled={busy} onClick={() => void act(() => moderationApi.resolveAccountReports(username))}>
            Classer les signalements
          </Button>
        </section>
      )}

      <div className={styles.panelActions}>
        {data.status === 'active' && (
          <ButtonLink to={`/u/${data.username}`} variant="secondary" fullWidth>
            Voir le profil public
          </ButtonLink>
        )}
        {!targetIsSuperAdmin &&
          (data.role === 'moderator' ? (
            <Button
              variant="secondary"
              fullWidth
              disabled={busy || !canChangeRole}
              title={roleDisabledTitle}
              onClick={() =>
                void act(
                  () => moderationApi.setRole(username, 'user'),
                  `Retirer le rôle de modérateur à ${data.display_name} ?`,
                )
              }
            >
              Retirer le rôle de modérateur
            </Button>
          ) : (
            <Button
              variant="secondary"
              fullWidth
              disabled={busy || !canChangeRole || data.status !== 'active'}
              title={roleDisabledTitle}
              onClick={() =>
                void act(
                  () => moderationApi.setRole(username, 'moderator'),
                  `Promouvoir ${data.display_name} modérateur ?`,
                )
              }
            >
              Promouvoir modérateur
            </Button>
          ))}
        {data.status === 'suspended' ? (
          <Button
            variant="secondary"
            fullWidth
            disabled={busy || !canSanction}
            title={sanctionDisabledTitle}
            onClick={() => void act(() => moderationApi.reactivate(username))}
          >
            Réactiver le compte
          </Button>
        ) : (
          <Button
            variant="danger"
            fullWidth
            disabled={busy || !canSanction}
            title={sanctionDisabledTitle}
            onClick={() =>
              void act(
                () => moderationApi.suspend(username),
                `Suspendre le compte de ${data.display_name} ? Il sera déconnecté.`,
              )
            }
          >
            Suspendre le compte
          </Button>
        )}
        <Button
          variant="danger"
          fullWidth
          disabled={busy || !canSanction}
          title={sanctionDisabledTitle}
          onClick={() =>
            void act(async () => {
              await moderationApi.deleteAccount(username)
              onDeleted()
            }, `Supprimer définitivement le compte de ${data.display_name}, ses posts et ses sorties ?`)
          }
        >
          Supprimer le compte
        </Button>
      </div>
    </aside>
  )
}
