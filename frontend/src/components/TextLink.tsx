import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { cx } from '../lib/cx'
import styles from './TextLink.module.css'

type TextLinkProps = { children: ReactNode; className?: string } & (
  | { to: string; onClick?: never; disabled?: never }
  | { to?: never; onClick: () => void; disabled?: boolean }
)

/** Lien texte vert en 14 px Semi Bold (« Mot de passe oublié ? », « ← Mon profil »). */
export function TextLink({ children, className, ...props }: TextLinkProps) {
  if (props.to !== undefined) {
    return (
      <Link to={props.to} className={cx(styles.link, className)}>
        {children}
      </Link>
    )
  }
  return (
    <button type="button" className={cx(styles.link, styles.button, className)} onClick={props.onClick} disabled={props.disabled}>
      {children}
    </button>
  )
}
