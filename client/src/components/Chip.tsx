import type { ComponentProps } from 'react'
import { cx } from '../lib/cx'
import styles from './Chip.module.css'

type ChipProps = ComponentProps<'button'> & {
  selected?: boolean
  /** « sm » : filtres des écrans de modération. */
  size?: 'md' | 'sm'
}

/** Filtre cliquable (Tous / Gardés / Non gardés…). */
export function Chip({ selected = false, size = 'md', type = 'button', className, ...rest }: ChipProps) {
  return (
    <button
      type={type}
      aria-pressed={selected}
      className={cx(styles.chip, styles[size], selected && styles.selected, className)}
      {...rest}
    />
  )
}
