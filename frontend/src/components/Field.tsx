import type { ReactNode } from 'react'
import styles from './Field.module.css'

type FieldProps = {
  id: string
  label?: ReactNode
  hint?: ReactNode
  error?: ReactNode
  children: ReactNode
}

/** Libellé, champ, puis aide ou message d'erreur. Partagé par Input et Select. */
export function Field({ id, label, hint, error, children }: FieldProps) {
  return (
    <div className={styles.field}>
      {label && (
        <label className={styles.label} htmlFor={id}>
          {label}
        </label>
      )}
      {children}
      {error ? (
        <p id={`${id}-message`} className={styles.error}>
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${id}-message`} className={styles.hint}>
            {hint}
          </p>
        )
      )}
    </div>
  )
}
