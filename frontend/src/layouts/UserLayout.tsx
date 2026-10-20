import { Outlet } from 'react-router'
import { useAuth } from '../auth/context'
import { Navbar } from '../components'
import styles from './UserLayout.module.css'

type UserLayoutProps = {
  /** Contenu pleine largeur et pleine hauteur, sans marges (écran 03 · Carte). */
  fullBleed?: boolean
  /** Pleine largeur, hauteur libre : la page gère ses marges (bannière de l'écran 08). */
  edgeToEdge?: boolean
}

/** Pages utilisateur : barre de navigation et contenu de 1200 px centré. À placer sous RequireActive. */
export function UserLayout({ fullBleed = false, edgeToEdge = false }: UserLayoutProps) {
  const { me } = useAuth()
  if (!me) return null
  return (
    <>
      <Navbar user={{ name: me.user.display_name, role: me.user.role }} />
      <main className={fullBleed ? styles.fullBleed : edgeToEdge ? undefined : styles.page}>
        <Outlet />
      </main>
    </>
  )
}
