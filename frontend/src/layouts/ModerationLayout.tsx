import { Outlet, useLocation } from 'react-router'
import { moderationApi } from '../api/moderation'
import { useAuth } from '../auth/context'
import { ModerationSidebar } from '../components'
import { useApi } from '../lib/useApi'
import styles from './ModerationLayout.module.css'

/** Écrans de modération : barre latérale de 260 px et contenu. À placer sous RequireModerator. */
export function ModerationLayout() {
  const { me } = useAuth()
  // Rechargé à chaque changement de page : le compteur suit les signalements classés.
  const { pathname } = useLocation()
  const summary = useApi(`moderation-summary:${pathname}`, moderationApi.summary, '')
  if (!me) return null
  return (
    <div className={styles.layout}>
      <ModerationSidebar openReports={summary.data?.open_reports ?? 0} user={{ name: me.user.display_name, roleLabel: 'Modération' }} />
      <main className={styles.content}>
        <Outlet />
      </main>
    </div>
  )
}
