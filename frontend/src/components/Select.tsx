import { ChevronDown } from 'lucide-react'
import { useId, type ComponentProps, type ReactNode } from 'react'
import { cx } from '../lib/cx'
import { Field } from './Field'
import inputStyles from './Input.module.css'
import styles from './Select.module.css'

export type SelectOption = { value: string; label: string }

type SelectProps = Omit<ComponentProps<'select'>, 'children' | 'size'> & {
  options: SelectOption[]
  label?: ReactNode
  hint?: ReactNode
  error?: ReactNode
  /** « sm » : liste compacte des réglages (14 px Medium, écran 05c). */
  size?: 'md' | 'sm'
}

export function Select({ options, label, hint, error, size = 'md', id, className, ...rest }: SelectProps) {
  const generatedId = useId()
  const selectId = id ?? generatedId
  return (
    <Field id={selectId} label={label} hint={hint} error={error}>
      <div className={inputStyles.wrapper}>
        <select
          id={selectId}
          className={cx(inputStyles.input, styles.select, size === 'sm' && styles.sm, error !== undefined && inputStyles.invalid, className)}
          aria-invalid={error !== undefined || undefined}
          aria-describedby={error || hint ? `${selectId}-message` : undefined}
          {...rest}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown aria-hidden className={styles.chevron} size={size === 'sm' ? 14 : 16} />
      </div>
    </Field>
  )
}
