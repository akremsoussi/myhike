import { formatNumber } from '../lib/format'
import styles from './StatBlock.module.css'

type StatBlockProps = {
  value: number
  label: string
}

/** Chiffre et libellé centrés de l'en-tête de profil (Sorties, Posts, Communautés, Amis). */
export function StatBlock({ value, label }: StatBlockProps) {
  return (
    <div className={styles.stat}>
      <span className={styles.value}>{formatNumber(value)}</span>
      <span className={styles.label}>{label}</span>
    </div>
  )
}
