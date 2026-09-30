import { Link } from 'react-router'
import { cx } from '../lib/cx'
import styles from './Logo.module.css'

type LogoProps = {
  to?: string
  /** « onDark » : sur le fond vert foncé de la barre de modération. */
  variant?: 'default' | 'onDark'
  /** « lg » : panneau vert des pages de connexion (carré de 40 px, 22 px). */
  size?: 'md' | 'lg'
}

export function Logo({ to = '/carte', variant = 'default', size = 'md' }: LogoProps) {
  return (
    <Link to={to} className={cx(styles.logo, styles[variant], size === 'lg' && styles.lg)}>
      <span className={styles.mark} aria-hidden>
        R
      </span>
      Refuges
    </Link>
  )
}
