import { MapPin, Search, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { refugesApi, type RefugeSummary } from '../../api/refuges'
import { Input } from '../../components'
import { formatAltitude } from '../../lib/format'
import styles from './RefugeField.module.css'

const SEARCH_LIMIT = 6

export type ChosenRefuge = { id: number; name: string }

type RefugeFieldProps = {
  value: ChosenRefuge | null
  onChange: (refuge: ChosenRefuge | null) => void
  error?: string
}

/** « Refuge (optionnel) » : le post apparaîtra dans « Voir les posts liés » de sa fiche. */
export function RefugeField({ value, onChange, error }: RefugeFieldProps) {
  const [search, setSearch] = useState('')
  const [results, setResults] = useState<RefugeSummary[]>([])
  const term = search.trim()

  useEffect(() => {
    if (term.length < 2) return
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      refugesApi
        .list({ q: term, limit: SEARCH_LIMIT }, controller.signal)
        .then((list) => setResults(list.items))
        .catch(() => undefined)
    }, 250)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [term])

  if (value) {
    return (
      <div className={styles.chosen}>
        <MapPin aria-hidden size={16} className={styles.pin} />
        <span className={styles.name}>{value.name}</span>
        <button type="button" className={styles.clear} aria-label={`Retirer ${value.name}`} onClick={() => onChange(null)}>
          <X aria-hidden size={14} />
        </button>
      </div>
    )
  }

  return (
    <div className={styles.picker}>
      <Input
        type="search"
        aria-label="Rechercher un refuge"
        placeholder="Rechercher un refuge…"
        icon={<Search aria-hidden size={16} />}
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        error={error}
        hint={error ? undefined : 'Le post apparaîtra aussi sur la fiche du refuge.'}
      />
      {term.length >= 2 && (
        <ul className={styles.results}>
          {results.map((refuge) => (
            <li key={refuge.id}>
              <button
                type="button"
                className={styles.result}
                onClick={() => {
                  onChange({ id: refuge.id, name: refuge.name })
                  setSearch('')
                }}
              >
                <span>{refuge.name}</span>
                <span className={styles.meta}>
                  {[refuge.massif?.name, refuge.altitude && formatAltitude(refuge.altitude)].filter(Boolean).join(' · ')}
                </span>
              </button>
            </li>
          ))}
          {results.length === 0 && <li className={styles.meta}>Aucun refuge trouvé.</li>}
        </ul>
      )}
    </div>
  )
}
