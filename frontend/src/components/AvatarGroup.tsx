import { Avatar, type AvatarSize } from './Avatar'
import styles from './AvatarGroup.module.css'

type AvatarGroupProps = {
  names: string[]
  size?: AvatarSize
  /** Nombre maximal d'avatars affichés. */
  max?: number
}

/** Avatars qui se chevauchent (participants d'une sortie, aperçu des amis). */
export function AvatarGroup({ names, size = 'sm', max = 3 }: AvatarGroupProps) {
  return (
    <div className={styles.group}>
      {names.slice(0, max).map((name, index) => (
        <span key={`${name}-${index}`} className={styles.item}>
          <Avatar name={name} size={size} />
        </span>
      ))}
    </div>
  )
}
