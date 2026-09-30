import type { Ref } from 'react'
import type { RefugeSummary } from '../../api/refuges'
import { StatusBadge } from '../../components'
import { cx } from '../../lib/cx'
import styles from './MapPage.module.css'
import { altitudeAndCapacity, guardLabel, isClosed } from './refugeText'

type RefugeListItemProps = {
  refuge: RefugeSummary
  selected: boolean
  onSelect: (refuge: RefugeSummary) => void
  ref?: Ref<HTMLButtonElement>
}

/** Carte d'un refuge dans la liste de gauche (écran 03). */
export function RefugeListItem({ refuge, selected, onSelect, ref }: RefugeListItemProps) {
  const meta = [refuge.massif?.name, ...altitudeAndCapacity(refuge)].filter(Boolean).join(' · ')
  return (
    <button
      ref={ref}
      type="button"
      className={cx(styles.item, selected && styles.itemSelected)}
      onClick={() => onSelect(refuge)}
      aria-pressed={selected}
    >
      <span className={styles.itemImage} aria-hidden />
      <span className={styles.itemText}>
        <span className={styles.itemName}>{refuge.name}</span>
        {meta && <span className={styles.itemMeta}>{meta}</span>}
      </span>
      <StatusBadge tone={refuge.is_guarded && !isClosed(refuge) ? 'success' : 'neutral'}>{guardLabel(refuge)}</StatusBadge>
    </button>
  )
}
