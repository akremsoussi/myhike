import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { Card, StatusBadge, type StatusTone } from '../components'
import styles from './StatusPage.module.css'

type Health = { api: 'ok'; database: 'ok' | 'error' }
type Status = 'pending' | 'ok' | 'error'

const BADGES: Record<Status, { tone: StatusTone; label: string }> = {
  pending: { tone: 'neutral', label: 'Vérification…' },
  ok: { tone: 'success', label: 'OK' },
  error: { tone: 'danger', label: 'Erreur' },
}

function StatusRow({ label, status }: { label: string; status: Status }) {
  const badge = BADGES[status]
  return (
    <div className={styles.row}>
      <span>{label}</span>
      <StatusBadge tone={badge.tone}>{badge.label}</StatusBadge>
    </div>
  )
}

/** Page technique : vérifie que le front joint l'API et la base. */
export function StatusPage() {
  const [api, setApi] = useState<Status>('pending')
  const [database, setDatabase] = useState<Status>('pending')

  useEffect(() => {
    fetch('/api/health')
      .then((response) => response.json() as Promise<Health>)
      .then((health) => {
        setApi('ok')
        setDatabase(health.database)
      })
      .catch(() => {
        setApi('error')
        setDatabase('error')
      })
  }, [])

  return (
    <main className={styles.page}>
      <h1 className={styles.title}>Refuges</h1>
      <Card>
        <StatusRow label="API FastAPI" status={api} />
        <StatusRow label="Base MySQL" status={database} />
      </Card>
      <Link to="/demo" className={styles.link}>
        Voir les composants →
      </Link>
    </main>
  )
}
