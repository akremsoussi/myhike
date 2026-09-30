import type { ReactNode } from 'react'
import { cx } from '../lib/cx'
import styles from './Card.module.css'

type CardProps = {
  /** compact : cartes de liste · large : en-tête de profil, formulaires de modération. */
  padding?: 'default' | 'compact' | 'large'
  title?: ReactNode
  /** Élément aligné à droite du titre (lien « Tout voir », bouton…). */
  action?: ReactNode
  className?: string
  children: ReactNode
}

/** Carte de contenu : bordure de 1 px, sans ombre. */
export function Card({ padding = 'default', title, action, className, children }: CardProps) {
  return (
    <section className={cx(styles.card, styles[padding], className)}>
      {(title || action) && (
        <header className={styles.header}>
          {title && <h2 className={styles.title}>{title}</h2>}
          {action}
        </header>
      )}
      {children}
    </section>
  )
}
