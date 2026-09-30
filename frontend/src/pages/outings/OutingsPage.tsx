import { Plus } from 'lucide-react'
import { useState } from 'react'
import { outingsApi, type OutingScope } from '../../api/outings'
import { useAuth } from '../../auth/context'
import { ButtonLink, Chip, Notice, OutingCard } from '../../components'
import { useApi } from '../../lib/useApi'
import styles from './OutingsPage.module.css'

const TABS: { value: OutingScope; label: string; empty: string }[] = [
  { value: 'upcoming', label: 'À venir', empty: 'Aucune sortie à venir. Proposez la première !' },
  { value: 'mine', label: 'Mes sorties', empty: 'Vous n’organisez aucune sortie à venir.' },
  { value: 'joined', label: 'Où je participe', empty: 'Vous ne participez à aucune autre sortie à venir.' },
  { value: 'past', label: 'Passées', empty: 'Aucune sortie passée.' },
]

/** Écran 10 · Sorties. */
export function OutingsPage() {
  const { me } = useAuth()
  const [scope, setScope] = useState<OutingScope>('upcoming')
  const outings = useApi(`outings:${scope}`, () => outingsApi.list(scope), 'Les sorties n’ont pas pu être chargées.')
  const tab = TABS.find((item) => item.value === scope)!

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.intro}>
          <h1 className={styles.title}>Sorties</h1>
          <p className={styles.lead}>Organisez-vous entre randonneurs : chemin, points de stop et participants.</p>
        </div>
        <ButtonLink to="/sorties/nouvelle" icon={<Plus aria-hidden size={16} />}>
          Créer une sortie
        </ButtonLink>
      </header>

      <div className={styles.filters} role="group" aria-label="Filtrer les sorties">
        {TABS.map((item) => (
          <Chip key={item.value} selected={scope === item.value} onClick={() => setScope(item.value)}>
            {item.label}
          </Chip>
        ))}
      </div>

      {outings.error && <Notice tone="danger">{outings.error}</Notice>}
      <div className={styles.grid}>
        {outings.data?.map((outing) => (
          <OutingCard key={outing.id} outing={outing} viewerUsername={me?.user.username} />
        ))}
      </div>
      {!outings.loading && outings.data?.length === 0 && <p className={styles.empty}>{tab.empty}</p>}
    </div>
  )
}
