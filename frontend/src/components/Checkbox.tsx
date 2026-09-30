import { Check } from 'lucide-react'
import type { ComponentProps, ReactNode } from 'react'
import styles from './Checkbox.module.css'

type CheckboxProps = Omit<ComponentProps<'input'>, 'type'> & {
  children: ReactNode
  error?: ReactNode
}

/** Case à cocher de 20 px (« J'accepte les conditions d'utilisation »). */
export function Checkbox({ children, error, className, ...rest }: CheckboxProps) {
  return (
    <div className={className}>
      <label className={styles.checkbox}>
        <input type="checkbox" className={styles.input} aria-invalid={error ? true : undefined} {...rest} />
        <span className={styles.box} aria-hidden>
          <Check size={14} strokeWidth={3} />
        </span>
        <span className={styles.label}>{children}</span>
      </label>
      {error && <p className={styles.error}>{error}</p>}
    </div>
  )
}
