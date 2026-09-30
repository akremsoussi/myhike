import { moderationApi } from '../../api/moderation'
import { ButtonLink, Button, Card, Notice } from '../../components'
import { formatCount } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import common from './moderation.module.css'
import { ReportItem } from './ReportItem'
import styles from './ReportsPage.module.css'

/** Signalements à traiter (page absente de la maquette, construite avec les mêmes éléments). */
export function ReportsPage() {
  const reports = useApi('mod-reports', moderationApi.reports, 'Les signalements n’ont pas pu être chargés.')
  const list = reports.data ?? []

  async function act(action: () => Promise<void>, confirmMessage?: string) {
    if (confirmMessage && !window.confirm(confirmMessage)) return
    await action()
    reports.reload()
  }

  return (
    <div className={common.page}>
      <header className={common.header}>
        <div className={common.intro}>
          <h1 className={common.title}>Signalements</h1>
          <p className={common.lead}>{formatCount(list.length, 'signalement à traiter', 'signalements à traiter')}</p>
        </div>
      </header>
      {reports.error && <Notice tone="danger">{reports.error}</Notice>}
      {!reports.loading && list.length === 0 && <p className={common.muted}>Aucun signalement en attente.</p>}
      <div className={styles.list}>
        {list.map((report) => (
          <Card key={report.id}>
            <ReportItem
              report={report}
              onDeletePost={() => void act(() => moderationApi.deletePost(report.post!.id), 'Supprimer ce post ?')}
            />
            <div className={common.rowActions}>
              <ButtonLink to={`/moderation/comptes?compte=${report.target.username}`} size="sm" variant="secondary">
                Examiner le compte
              </ButtonLink>
              <Button size="sm" variant="secondary" onClick={() => void act(() => moderationApi.resolveReport(report.id))}>
                Classer
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
