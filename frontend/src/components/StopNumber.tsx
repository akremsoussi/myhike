import { cx } from '../lib/cx'
import styles from './StopNumber.module.css'

type StopNumberProps = {
  value: number
  /** sm : 24 px (écran 12) · md : 28 px (liste de l'écran 11) · lg : 32 px (sur la carte). */
  size?: 'sm' | 'md' | 'lg'
}

/** Pastille numérotée d'un point de stop. */
export function StopNumber({ value, size = 'md' }: StopNumberProps) {
  return <span className={cx(styles.stop, styles[size])}>{value}</span>
}
