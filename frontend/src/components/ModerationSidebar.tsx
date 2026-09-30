import { ArrowUpRight, Flag, LayoutDashboard, Mountain, UserCog } from 'lucide-react'
import { Link, NavLink } from 'react-router'
import { cx } from '../lib/cx'
import { formatNumber } from '../lib/format'
import { Avatar } from './Avatar'
import { Logo } from './Logo'
import styles from './ModerationSidebar.module.css'
import { StatusBadge } from './StatusBadge'

type ModerationSidebarProps = {
  /** Signalements à traiter : compteur rouge, masqué à zéro. */
  openReports: number
  user: { name: string; roleLabel: string; avatarUrl?: string }
}

export function ModerationSidebar({ openReports, user }: ModerationSidebarProps) {
  const links = [
    { to: '/moderation', label: 'Tableau de bord', icon: LayoutDashboard, end: true },
    { to: '/moderation/communautes', label: 'Communautés', icon: Mountain },
    { to: '/moderation/comptes', label: 'Comptes', icon: UserCog },
    { to: '/moderation/signalements', label: 'Signalements', icon: Flag, count: openReports },
  ]

  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <Logo to="/moderation" variant="onDark" />
        <StatusBadge tone="accent" size="xs">
          Modération
        </StatusBadge>
      </div>
      <nav className={styles.links} aria-label="Modération">
        {links.map(({ to, label, icon: Icon, end, count }) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => cx(styles.link, isActive && styles.active)}>
            <Icon aria-hidden size={16} className={styles.icon} />
            <span className={styles.label}>{label}</span>
            {count !== undefined && count > 0 && (
              <span className={styles.count} aria-label={`${count} à traiter`}>
                {formatNumber(count)}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
      <Link to="/carte" className={styles.publicLink}>
        <ArrowUpRight aria-hidden size={14} />
        Voir le site public
      </Link>
      <div className={styles.user}>
        <Avatar name={user.name} src={user.avatarUrl} size="lg" />
        <div className={styles.userText}>
          <span className={styles.userName}>{user.name}</span>
          <span className={styles.userRole}>{user.roleLabel}</span>
        </div>
      </div>
    </aside>
  )
}
