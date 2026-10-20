import type { ReactNode } from 'react'
import { Link, type LinkProps } from 'react-router'
import { cx } from '../lib/cx'
import styles from './Button.module.css'

type ButtonLinkProps = LinkProps & {
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'md' | 'sm'
  icon?: ReactNode
  fullWidth?: boolean
}

/** Lien de navigation avec l'apparence d'un bouton (« Voir la fiche »). */
export function ButtonLink({
  variant = 'primary',
  size = 'md',
  icon,
  fullWidth = false,
  className,
  children,
  ...rest
}: ButtonLinkProps) {
  return (
    <Link
      className={cx(styles.button, styles[variant], styles[size], fullWidth && styles.fullWidth, styles.link, className)}
      {...rest}
    >
      {icon}
      {children}
    </Link>
  )
}
