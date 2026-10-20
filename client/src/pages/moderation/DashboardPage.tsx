import { Plus } from 'lucide-react'
import { moderationApi, REPORT_REASONS } from '../../api/moderation'
import { ButtonLink, Card, Notice, StatCard, UserRow } from '../../components'
import { formatCount, formatRelative, shortName } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import styles from './DashboardPage.module.css'
import common from './moderation.module.css'

/** Écran 13 · Tableau de bord de modération. */
export function DashboardPage() {
  const dashboard = useApi('moderation-dashboard', moderationApi.dashboard, 'Le tableau de bord n’a pas pu être chargé.')
  const data = dashboard.data

  return (
    <div className={common.page}>
      <header className={common.header}>
        <div className={common.intro}>
          <h1 className={common.title}>Tableau de bord</h1>
          <p className={common.lead}>Vue d’ensemble de la plateforme</p>
        </div>
        <ButtonLink to="/moderation/communautes/nouvelle" icon={<Plus aria-hidden size={16} />}>
          Créer une communauté
        </ButtonLink>
      </header>

      {dashboard.error && <Notice tone="danger">{dashboard.error}</Notice>}
      {data && (
        <>
          <div className={styles.stats}>
            <StatCard label="Utilisateurs" value={data.users.value} note={`+${data.users.recent} cette semaine`} />
            <StatCard label="Communautés" value={data.communities.value} note={`+${data.communities.recent} ce mois-ci`} />
            <StatCard label="Sorties actives" value={data.active_outings.value} note={`${data.active_outings.recent} ce week-end`} />
            <StatCard label="Comptes signalés" value={data.reported_accounts} note="à traiter" tone="danger" />
          </div>

          <div className={`${common.columns} ${styles.columns}`}>
            <Card title={<span className={common.sectionTitle}>Activité récente</span>}>
              {data.activity.length === 0 && <p className={common.muted}>Aucune activité pour l’instant.</p>}
              <ul className={styles.activity}>
                {data.activity.map((item, index) => (
                  <li key={`${item.created_at}-${index}`} className={styles.event}>
                    <span className={styles.dot} aria-hidden />
                    <span className={styles.eventText}>
                      <span className={styles.eventMessage}>{item.message}</span>
                      <span className={styles.eventMeta}>
                        {item.actor && `par ${shortName(item.actor.display_name)} · `}
                        {formatRelative(item.created_at)}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </Card>

            <div className={common.aside}>
              <Card title={<span className={common.sectionTitle}>Signalements à traiter</span>}>
                {data.reported.length === 0 && <p className={common.muted}>Aucun signalement en attente.</p>}
                {data.reported.map((account) => {
                  const where = account.last_community ? ` dans « ${account.last_community.name} »` : ''
                  return (
                    <UserRow
                      key={account.user.username}
                      name={account.user.display_name}
                      username={account.user.username}
                      meta={`${REPORT_REASONS[account.last_reason]}${where} · ${formatCount(account.report_count, 'signalement')}`}
                      compact
                      actions={
                        <ButtonLink to={`/moderation/comptes?compte=${account.user.username}`} size="sm" variant="secondary">
                          Examiner
                        </ButtonLink>
                      }
                    />
                  )
                })}
              </Card>
              <Card title={<span className={common.sectionTitle}>Actions rapides</span>}>
                <ButtonLink to="/moderation/communautes" variant="secondary" fullWidth>
                  Gérer les communautés
                </ButtonLink>
                <ButtonLink to="/moderation/comptes" variant="secondary" fullWidth>
                  Gérer les comptes
                </ButtonLink>
              </Card>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
