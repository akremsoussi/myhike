import { cx } from '../lib/cx'
import { formatNumber } from '../lib/format'
import styles from './Tabs.module.css'

export type Tab<T extends string> = {
  value: T
  label: string
  count?: number
  /** « pending » : compteur orange (demandes reçues à traiter). */
  countTone?: 'neutral' | 'pending'
}

type TabsProps<T extends string> = {
  tabs: Tab<T>[]
  value: T
  onChange: (value: T) => void
  'aria-label': string
}

/** Onglets de page (Mes amis / Demandes reçues / Demandes envoyées). */
export function Tabs<T extends string>({ tabs, value, onChange, 'aria-label': ariaLabel }: TabsProps<T>) {
  return (
    <div className={styles.tabs} role="tablist" aria-label={ariaLabel}>
      {tabs.map((tab) => {
        const active = tab.value === value
        return (
          <button
            key={tab.value}
            type="button"
            role="tab"
            aria-selected={active}
            className={cx(styles.tab, active && styles.active)}
            onClick={() => onChange(tab.value)}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span className={cx(styles.count, styles[tab.countTone ?? 'neutral'])}>{formatNumber(tab.count)}</span>
            )}
          </button>
        )
      })}
    </div>
  )
}
