import { Outlet } from 'react-router'
import { Logo } from '../components'
import styles from './AuthLayout.module.css'

/** Pages de connexion (01, 02, 02b) : panneau vert de 800 px et formulaire de 420 px centré. */
export function AuthLayout() {
  return (
    <div className={styles.layout}>
      <aside className={styles.visual}>
        <Logo to="/connexion" variant="onDark" size="lg" />
        <div className={styles.pitch}>
          <p className={styles.tagline}>
            Trouvez un refuge,
            <br />
            partagez vos chemins,
            <br />
            partez ensemble.
          </p>
          <p className={styles.lead}>
            La carte des refuges de montagne, des communautés par massif et des sorties organisées entre randonneurs.
          </p>
        </div>
        {/* Chiffres de la maquette : à brancher sur l'API quand les refuges et communautés existeront. */}
        <p className={styles.stats}>1 200 refuges · 24 communautés · 2 300 randonneurs</p>
      </aside>
      <main className={styles.content}>
        <div className={styles.form}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}
