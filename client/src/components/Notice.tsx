import type { ReactNode } from 'react'
import { cx } from '../lib/cx'
import styles from './Notice.module.css'

type NoticeProps = {
  /** info : encadré vert clair (écran 05c) ; danger : erreur. */
  tone?: 'info' | 'danger'
  icon?: ReactNode
  children: ReactNode
}

/** Encadré d'information ou d'erreur. */
export function Notice({ tone = 'info', icon, children }: NoticeProps) {
  return (
    <div className={cx(styles.notice, styles[tone])} role={tone === 'danger' ? 'alert' : 'status'}>
      {icon && <span className={styles.icon}>{icon}</span>}
      <div className={styles.text}>{children}</div>
    </div>
  )
}
