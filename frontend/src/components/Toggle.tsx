import { cx } from '../lib/cx'
import styles from './Toggle.module.css'

type ToggleProps = {
  checked: boolean
  onChange: (checked: boolean) => void
  /** Libellé lu par les lecteurs d'écran quand aucun texte visible n'accompagne l'interrupteur. */
  'aria-label'?: string
  'aria-labelledby'?: string
  disabled?: boolean
}

export function Toggle({ checked, onChange, disabled, ...aria }: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      className={cx(styles.toggle, checked && styles.on)}
      onClick={() => onChange(!checked)}
      {...aria}
    >
      <span className={styles.knob} />
    </button>
  )
}
