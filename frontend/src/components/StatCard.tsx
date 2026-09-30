import { cx } from '../lib/cx'
import { formatNumber } from '../lib/format'
import styles from './StatCard.module.css'

type StatCardProps = {
  label: string
  value: number
  /** Ligne sous le chiffre (« +142 cette semaine », « à traiter »). */
  note?: string
  /** « danger » : carte rouge (« Comptes signalés »). */
  tone?: 'default' | 'danger'
}

/** Carte de statistique du tableau de bord de modération. */
export function StatCard({ label, value, note, tone = 'default' }: StatCardProps) {
  return (
    <div className={cx(styles.card, styles[tone])}>
      <span className={styles.label}>{label}</span>
      <span className={styles.value}>{formatNumber(value)}</span>
      {note && <span className={styles.note}>{note}</span>}
    </div>
  )
}
