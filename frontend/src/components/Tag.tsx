import type { ReactNode } from 'react'
import { cx } from '../lib/cx'
import styles from './Tag.module.css'

type TagProps = {
  /** filled : fond vert (« Gardé ») · outline : contour gris (« 2 542 m », « Alpes »). */
  tone?: 'outline' | 'filled'
  children: ReactNode
}

/** Pastille d'information, même apparence qu'un Chip mais non cliquable. */
export function Tag({ tone = 'outline', children }: TagProps) {
  return <span className={cx(styles.tag, styles[tone])}>{children}</span>
}
