import { ArrowLeft, Lock } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Link } from 'react-router'
import { usersApi, type Audience, type PrivacySettings, type RequestPolicy } from '../../api/users'
import { Button, Notice, SegmentedControl, Select, Toggle, type Visibility } from '../../components'
import { ApiError } from '../../lib/api'
import { cx } from '../../lib/cx'
import { useApi } from '../../lib/useApi'
import styles from './PrivacySettingsPage.module.css'

const AUDIENCES: { value: Audience; label: string }[] = [
  { value: 'everyone', label: 'Tout le monde' },
  { value: 'friends', label: 'Mes amis' },
  { value: 'me', label: 'Moi uniquement' },
]

const REQUEST_POLICIES: { value: RequestPolicy; label: string }[] = [
  { value: 'everyone', label: 'Tout le monde' },
  { value: 'communities', label: 'Membres de mes communautés' },
]

// Sections pas encore dessinées : visibles mais inactives.
const MENU = [
  { label: 'Profil', active: false },
  { label: 'Confidentialité', active: true },
  { label: 'Compte & sécurité', active: false },
  { label: 'Notifications', active: false },
]

function Setting({ id, title, help, children }: { id: string; title: string; help: string; children: ReactNode }) {
  return (
    <div className={styles.setting}>
      <div className={styles.settingText}>
        <span id={id} className={styles.settingTitle}>
          {title}
        </span>
        <span className={styles.settingHelp}>{help}</span>
      </div>
      {children}
    </div>
  )
}

/** Écran 05c · Paramètres de confidentialité. */
export function PrivacySettingsPage() {
  const saved = useApi('privacy', usersApi.privacy, 'Vos paramètres n’ont pas pu être chargés.')
  // Brouillon : null tant que rien n'a été modifié depuis le dernier enregistrement.
  const [draft, setDraft] = useState<PrivacySettings | null>(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ tone: 'info' | 'danger'; text: string } | null>(null)

  const settings = draft ?? saved.data
  if (!settings) return saved.error ? <Notice tone="danger">{saved.error}</Notice> : null

  const change = <K extends keyof PrivacySettings>(key: K, value: PrivacySettings[K]) => {
    setDraft({ ...settings, [key]: value })
    setMessage(null)
  }

  async function save() {
    if (!draft) return
    setSaving(true)
    try {
      saved.setData(await usersApi.updatePrivacy(draft))
      setDraft(null)
      setMessage({ tone: 'info', text: 'Paramètres enregistrés.' })
    } catch (err) {
      setMessage({ tone: 'danger', text: err instanceof ApiError ? err.message : 'Les paramètres n’ont pas pu être enregistrés.' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={styles.page}>
      <Link to="/profil" className={styles.back}>
        <ArrowLeft aria-hidden size={14} />
        Mon profil
      </Link>
      <h1 className={styles.title}>Paramètres</h1>

      <div className={styles.columns}>
        <nav className={styles.menu} aria-label="Paramètres">
          {MENU.map((item) => (
            <span
              key={item.label}
              className={cx(styles.menuItem, item.active && styles.menuActive)}
              aria-current={item.active ? 'page' : undefined}
              aria-disabled={!item.active || undefined}
              title={item.active ? undefined : 'Bientôt disponible'}
            >
              {item.label}
            </span>
          ))}
        </nav>

        <section className={styles.panel}>
          <header className={styles.panelHeader}>
            <h2 className={styles.panelTitle}>Confidentialité</h2>
            <p className={styles.settingHelp}>Choisissez qui peut voir vos publications et votre activité.</p>
          </header>

          <Setting
            id="setting-visibility"
            title="Visibilité par défaut de mes posts"
            help="Appliquée à chaque nouveau post. Vous pouvez la changer au moment de publier."
          >
            <SegmentedControl<Visibility>
              aria-label="Visibilité par défaut de mes posts"
              value={settings.default_post_visibility}
              onChange={(value) => change('default_post_visibility', value)}
              segments={[
                { value: 'public', label: 'Public' },
                { value: 'friends', label: 'Amis uniquement', icon: <Lock aria-hidden size={14} /> },
              ]}
            />
          </Setting>
          <Setting id="setting-friends" title="Qui peut voir ma liste d’amis" help="Sur votre profil public.">
            <div className={styles.select}>
              <Select
                size="sm"
                aria-labelledby="setting-friends"
                value={settings.friends_list_audience}
                onChange={(event) => change('friends_list_audience', event.target.value as Audience)}
                options={AUDIENCES}
              />
            </div>
          </Setting>
          <Setting
            id="setting-outings"
            title="Qui peut voir mes sorties à venir"
            help="Les sorties ouvertes restent visibles dans l’onglet Sorties."
          >
            <div className={styles.select}>
              <Select
                size="sm"
                aria-labelledby="setting-outings"
                value={settings.outings_audience}
                onChange={(event) => change('outings_audience', event.target.value as Audience)}
                options={AUDIENCES}
              />
            </div>
          </Setting>
          <Setting
            id="setting-requests"
            title="Qui peut m’envoyer une demande d’ami"
            help="Limitez les demandes aux membres de vos communautés."
          >
            <div className={styles.select}>
              <Select
                size="sm"
                aria-labelledby="setting-requests"
                value={settings.friend_requests_from}
                onChange={(event) => change('friend_requests_from', event.target.value as RequestPolicy)}
                options={REQUEST_POLICIES}
              />
            </div>
          </Setting>
          <Setting
            id="setting-suggestions"
            title="Apparaître dans les suggestions d’amis"
            help="Proposé aux membres de vos communautés."
          >
            <Toggle
              aria-labelledby="setting-suggestions"
              checked={settings.show_in_suggestions}
              onChange={(value) => change('show_in_suggestions', value)}
            />
          </Setting>

          <Notice icon={<Lock aria-hidden size={18} />}>
            Un post « Amis uniquement » n’est visible que par vous et vos amis, y compris quand il est publié dans une
            communauté. Modifier la visibilité par défaut ne change pas vos anciens posts.
          </Notice>
          {message && <Notice tone={message.tone}>{message.text}</Notice>}

          <div className={styles.actions}>
            <Button
              variant="secondary"
              disabled={!draft || saving}
              onClick={() => {
                setDraft(null)
                setMessage(null)
              }}
            >
              Annuler
            </Button>
            <Button disabled={!draft || saving} onClick={() => void save()}>
              {saving ? 'Enregistrement…' : 'Enregistrer'}
            </Button>
          </div>
        </section>
      </div>
    </div>
  )
}
