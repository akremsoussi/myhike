import { Search } from 'lucide-react'
import { NavLink, useLocation } from 'react-router'
import { cx } from '../lib/cx'
import { shortName } from '../lib/format'
import { Avatar } from './Avatar'
import { Logo } from './Logo'
import styles from './Navbar.module.css'

// `also` : autres pages rattachées à l'onglet (fiche refuge sous Carte, « Nouveau post » sous Communautés).
const TABS = [
  { to: '/carte', label: 'Carte', also: ['/refuges'] },
  { to: '/communautes', label: 'Communautés', also: ['/posts'] },
  { to: '/sorties', label: 'Sorties', also: [] },
]

type NavbarProps = {
  user: { name: string; avatarUrl?: string }
}

/** Barre de navigation des pages utilisateur (69 px) : logo, onglets centrés, recherche et pastille du profil. */
export function Navbar({ user }: NavbarProps) {
  const { pathname } = useLocation()
  return (
    <header className={styles.navbar}>
      <Logo />
      <nav className={styles.tabs} aria-label="Navigation principale">
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) =>
              cx(styles.tab, (isActive || tab.also.some((prefix) => pathname.startsWith(`${prefix}/`))) && styles.active)
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>
      <div className={styles.end}>
        <form className={styles.search} role="search" onSubmit={(event) => event.preventDefault()}>
          <Search aria-hidden size={14} className={styles.searchIcon} />
          <input type="search" className={styles.searchInput} placeholder="Rechercher…" aria-label="Rechercher" />
        </form>
        {/* Pastille sur fond vert quand on est dans son profil ou ses paramètres (écrans 05, 05b, 05c). */}
        <NavLink
          to="/profil"
          className={({ isActive }) =>
            cx(styles.user, (isActive || pathname.startsWith('/parametres/')) && styles.userActive)
          }
        >
          <Avatar name={user.name} src={user.avatarUrl} size="md" />
          {shortName(user.name)}
        </NavLink>
      </div>
    </header>
  )
}
