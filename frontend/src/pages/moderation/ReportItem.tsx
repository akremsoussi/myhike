import { Link } from 'react-router'
import { REPORT_REASONS, type Report } from '../../api/moderation'
import { Button, VisibilityBadge } from '../../components'
import { formatRelative, shortName } from '../../lib/format'
import styles from './ReportItem.module.css'

type ReportItemProps = {
  report: Report
  /** Dans le panneau d'un compte : sans rappeler le compte visé. */
  compact?: boolean
  onDeletePost?: () => void
}

/** Un signalement : motif, auteur, date, et le post concerné s'il y en a un. */
export function ReportItem({ report, compact = false, onDeletePost }: ReportItemProps) {
  return (
    <article className={styles.report}>
      <p className={styles.head}>
        <span className={styles.reason}>{REPORT_REASONS[report.reason]}</span>
        {!compact && (
          <>
            {' '}
            · <Link to={`/moderation/comptes?compte=${report.target.username}`}>@{report.target.username}</Link>
          </>
        )}
      </p>
      <p className={styles.meta}>
        par {shortName(report.reporter.display_name)} · {formatRelative(report.created_at)}
      </p>
      {report.comment && <p className={styles.comment}>« {report.comment} »</p>}
      {report.post && (
        <div className={styles.post}>
          <p className={styles.postMeta}>
            <VisibilityBadge visibility={report.post.visibility} variant="meta" />
            {report.post.community && <span> · {report.post.community.name}</span>}
          </p>
          <p className={styles.postBody}>{report.post.body}</p>
          {onDeletePost && (
            <Button size="sm" variant="danger" onClick={onDeletePost}>
              Supprimer le post
            </Button>
          )}
        </div>
      )}
    </article>
  )
}
