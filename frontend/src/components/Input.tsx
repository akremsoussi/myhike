import { useId, type ComponentProps, type ReactNode } from 'react'
import { cx } from '../lib/cx'
import { Field } from './Field'
import styles from './Input.module.css'

type InputProps = ComponentProps<'input'> & {
  label?: ReactNode
  hint?: ReactNode
  error?: ReactNode
  /** Icône à gauche (loupe d'un champ de recherche…). */
  icon?: ReactNode
}

export function Input({ label, hint, error, icon, id, className, ...rest }: InputProps) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  return (
    <Field id={inputId} label={label} hint={hint} error={error}>
      <div className={styles.wrapper}>
        {icon && <span className={styles.icon}>{icon}</span>}
        <input
          id={inputId}
          className={cx(styles.input, icon !== undefined && styles.withIcon, error !== undefined && styles.invalid, className)}
          aria-invalid={error !== undefined || undefined}
          aria-describedby={error || hint ? `${inputId}-message` : undefined}
          {...rest}
        />
      </div>
    </Field>
  )
}
