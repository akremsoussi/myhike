import type { ReactNode } from 'react'
import { cx } from '../lib/cx'
import styles from './SegmentedControl.module.css'

export type Segment<T extends string> = { value: T; label: string; icon?: ReactNode }

type SegmentedControlProps<T extends string> = {
  segments: Segment<T>[]
  value: T
  onChange: (value: T) => void
  'aria-label': string
  /** Toute la largeur, options de même largeur (« Publier sur », écran 09). */
  fullWidth?: boolean
}

/** Choix exclusif entre quelques options (Public / Amis uniquement). */
export function SegmentedControl<T extends string>({
  segments,
  value,
  onChange,
  'aria-label': ariaLabel,
  fullWidth = false,
}: SegmentedControlProps<T>) {
  return (
    <div className={cx(styles.control, fullWidth && styles.fullWidth)} role="radiogroup" aria-label={ariaLabel}>
      {segments.map((segment) => (
        <button
          key={segment.value}
          type="button"
          role="radio"
          aria-checked={segment.value === value}
          className={cx(styles.segment, segment.value === value && styles.selected)}
          onClick={() => onChange(segment.value)}
        >
          {segment.icon}
          {segment.label}
        </button>
      ))}
    </div>
  )
}
