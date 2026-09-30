import type { ReactNode } from 'react'
import { cx } from '../lib/cx'
import styles from './ChoiceCards.module.css'

export type Choice<T extends string> = { value: T; label: string; description: string; icon?: ReactNode }

type ChoiceCardsProps<T extends string> = {
  choices: Choice<T>[]
  value: T
  onChange: (value: T) => void
  'aria-label': string
}

/** Choix exclusif sous forme de cartes avec description (visibilité d'un post, écran 09). */
export function ChoiceCards<T extends string>({ choices, value, onChange, 'aria-label': ariaLabel }: ChoiceCardsProps<T>) {
  return (
    <div className={styles.group} role="radiogroup" aria-label={ariaLabel}>
      {choices.map((choice) => {
        const selected = choice.value === value
        return (
          <button
            key={choice.value}
            type="button"
            role="radio"
            aria-checked={selected}
            className={cx(styles.card, selected && styles.selected)}
            onClick={() => onChange(choice.value)}
          >
            <span className={styles.radio} aria-hidden />
            <span className={styles.text}>
              <span className={styles.label}>
                {choice.icon}
                {choice.label}
              </span>
              <span className={styles.description}>{choice.description}</span>
            </span>
          </button>
        )
      })}
    </div>
  )
}
