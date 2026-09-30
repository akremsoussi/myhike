import { cx } from '../lib/cx'
import { initials } from '../lib/format'
import styles from './Avatar.module.css'

export type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl'

type AvatarProps = {
  name: string
  size?: AvatarSize
  src?: string
}

/** Avatar rond : photo si disponible, sinon initiales sur fond vert clair. */
export function Avatar({ name, size = 'md', src }: AvatarProps) {
  const className = cx(styles.avatar, styles[`size-${size}`])
  if (src) {
    return <img className={className} src={src} alt={name} />
  }
  return (
    <span className={className} role="img" aria-label={name}>
      {initials(name)}
    </span>
  )
}
