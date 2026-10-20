import { useId, type ComponentProps, type ReactNode } from 'react'
import { cx } from '../lib/cx'
import { Field } from './Field'
import inputStyles from './Input.module.css'
import styles from './Textarea.module.css'

type TextareaProps = ComponentProps<'textarea'> & {
  label?: ReactNode
  hint?: ReactNode
  error?: ReactNode
}

/** Champ de texte sur plusieurs lignes (description d'un post), 150 px de haut. */
export function Textarea({ label, hint, error, id, className, ...rest }: TextareaProps) {
  const generatedId = useId()
  const textareaId = id ?? generatedId
  return (
    <Field id={textareaId} label={label} hint={hint} error={error}>
      <textarea
        id={textareaId}
        className={cx(inputStyles.input, styles.textarea, error !== undefined && inputStyles.invalid, className)}
        aria-invalid={error !== undefined || undefined}
        aria-describedby={error || hint ? `${textareaId}-message` : undefined}
        {...rest}
      />
    </Field>
  )
}
