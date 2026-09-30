import { Check, Globe, Lock, Mail, Plus, Search, UserPlus } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import {
  Avatar,
  AvatarGroup,
  Button,
  Card,
  Checkbox,
  ChoiceCards,
  Chip,
  CommunityCard,
  Input,
  ModerationSidebar,
  Notice,
  OutingCard,
  PostCard,
  PostTile,
  ReportDialog,
  SegmentedControl,
  Select,
  StatBlock,
  StatCard,
  StatusBadge,
  StopNumber,
  Tabs,
  Tag,
  Textarea,
  TextLink,
  Toggle,
  UserRow,
  VisibilityBadge,
  type AvatarSize,
} from '../components'
import { colors } from '../styles/tokens'
import styles from './DemoPage.module.css'

const AVATAR_SIZES: AvatarSize[] = ['xs', 'sm', 'md', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl', '6xl']
const REFUGE_FILTERS = ['Tous', 'Gardés', 'Non gardés', 'Avec sortie']
const IN_FIVE_DAYS = new Date(Date.now() + 5 * 86_400_000).toISOString()
const DEMO_OUTING = {
  id: 0,
  title: 'Tour du Glacier Blanc',
  starts_at: IN_FIVE_DAYS,
  organizer: { username: 'camille', display_name: 'Camille Martin' },
  status: 'open' as const,
  participant_count: 5,
  max_participants: 8,
  stop_count: 3,
  participants_preview: [{ display_name: 'Camille Martin' }, { display_name: 'Lucas Durand' }, { display_name: 'Sarah Blanc' }],
  preview: [[44.918, 6.421], [44.929, 6.41], [44.934, 6.4005], [44.945, 6.379]] as [number, number][],
}
const TWO_HOURS_AGO = new Date(Date.now() - 2 * 3_600_000).toISOString()
const REGION_FILTERS = ['Toutes', 'Alpes', 'Pyrénées', 'Préalpes']

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>{title}</h2>
      {children}
    </section>
  )
}

function Row({ label, children }: { label?: string; children: ReactNode }) {
  return (
    <div className={styles.rowBlock}>
      {label && <span className={styles.rowLabel}>{label}</span>}
      <div className={styles.row}>{children}</div>
    </div>
  )
}

/** Catalogue des composants de base, pour les vérifier visuellement (route /demo). */
export function DemoPage() {
  const [refugeFilter, setRefugeFilter] = useState('Tous')
  const [regionFilter, setRegionFilter] = useState('Toutes')
  const [visibility, setVisibility] = useState<'public' | 'friends'>('public')
  const [friendsTab, setFriendsTab] = useState<'friends' | 'received' | 'sent'>('received')
  const [suggestions, setSuggestions] = useState(true)
  const [notifications, setNotifications] = useState(false)
  const [terms, setTerms] = useState(true)
  const [destination, setDestination] = useState<'profile' | 'community'>('community')
  const [joined, setJoined] = useState(true)
  const [liked, setLiked] = useState(false)
  const [reporting, setReporting] = useState(false)

  return (
    <div className={styles.page}>
      <header className={styles.intro}>
        <h1 className={styles.title}>Composants</h1>
        <p className={styles.lead}>
          Composants de base, construits uniquement avec les tokens de <code>styles/tokens.css</code>.
        </p>
      </header>

      <Section title="Boutons">
        <Card>
          <Row label="Taille normale (15 px)">
            <Button>Se connecter</Button>
            <Button variant="secondary">Modifier le profil</Button>
            <Button variant="danger">Se déconnecter</Button>
            <Button icon={<Plus aria-hidden size={16} />}>Publier</Button>
            <Button disabled>Désactivé</Button>
          </Row>
          <Row label="Petite taille (13 px)">
            <Button size="sm">Accepter</Button>
            <Button size="sm" variant="secondary">
              Refuser
            </Button>
            <Button size="sm" variant="danger">
              Supprimer
            </Button>
            <Button size="sm" variant="secondary" icon={<UserPlus aria-hidden size={14} />}>
              Ajouter
            </Button>
          </Row>
          <div className={styles.narrow}>
            <Button fullWidth>S'inscrire</Button>
          </div>
        </Card>
      </Section>

      <Section title="Chips et badges">
        <Card>
          <Row label="Filtres (cliquables)">
            {REFUGE_FILTERS.map((filter) => (
              <Chip key={filter} selected={filter === refugeFilter} onClick={() => setRefugeFilter(filter)}>
                {filter}
              </Chip>
            ))}
          </Row>
          <Row label="Filtres de modération (petite taille)">
            {REGION_FILTERS.map((filter) => (
              <Chip key={filter} size="sm" selected={filter === regionFilter} onClick={() => setRegionFilter(filter)}>
                {filter}
              </Chip>
            ))}
          </Row>
          <Row label="Statuts">
            <StatusBadge tone="success">Ouverte</StatusBadge>
            <StatusBadge tone="success">Gardé</StatusBadge>
            <StatusBadge tone="accent">Complète</StatusBadge>
            <StatusBadge tone="accent">Chemin</StatusBadge>
            <StatusBadge tone="danger">Signalé</StatusBadge>
            <StatusBadge tone="neutral">Non gardé</StatusBadge>
            <StatusBadge tone="neutral">Suspendu</StatusBadge>
            <StatusBadge tone="pending">En attente de confirmation</StatusBadge>
            <StatusBadge tone="success" icon={<Check aria-hidden size={14} />}>
              Inscrit
            </StatusBadge>
            <StatusBadge tone="accent" size="xs">
              Modérateur
            </StatusBadge>
            <StatusBadge tone="pending" size="count">
              2
            </StatusBadge>
          </Row>
          <Row label="Pastilles non cliquables (Tag)">
            <Tag tone="filled">Gardé</Tag>
            <Tag>2 542 m</Tag>
            <Tag>Alpes</Tag>
          </Row>
          <Row label="Visibilité">
            <VisibilityBadge visibility="public" />
            <VisibilityBadge visibility="friends" />
            <div className={styles.photo}>
              <VisibilityBadge visibility="public" variant="overlay" />
            </div>
            <div className={styles.pathThumb}>
              <VisibilityBadge visibility="friends" variant="overlay" />
            </div>
          </Row>
        </Card>
      </Section>

      <Section title="Avatars">
        <Card>
          <Row>
            {AVATAR_SIZES.map((size) => (
              <div key={size} className={styles.avatarSample}>
                <Avatar name="Camille Martin" size={size} />
                <span className={styles.rowLabel}>{size}</span>
              </div>
            ))}
          </Row>
        </Card>
      </Section>

      <Section title="Champs">
        <Card>
          <div className={styles.fields}>
            <Input label="Email" type="email" placeholder="nom@exemple.com" icon={<Mail aria-hidden size={16} />} />
            <Input label="Mot de passe" type="password" placeholder="8 caractères min." />
            <Input label="Nom d'utilisateur" defaultValue="camille_m" error="Ce nom d'utilisateur est déjà pris." />
            <Select
              label="Massif"
              defaultValue="ecrins"
              options={[
                { value: 'ecrins', label: 'Écrins' },
                { value: 'vanoise', label: 'Vanoise' },
                { value: 'chartreuse', label: 'Chartreuse' },
              ]}
            />
            <Input label="Recherche" type="search" placeholder="Rechercher un refuge…" icon={<Search aria-hidden size={16} />} />
            <Input label="Désactivé" disabled defaultValue="camille@exemple.fr" />
            <Checkbox checked={terms} onChange={(event) => setTerms(event.target.checked)}>
              J'accepte les conditions d'utilisation
            </Checkbox>
            <Checkbox checked={false} onChange={() => undefined} error="Vous devez accepter les conditions d'utilisation.">
              Case en erreur
            </Checkbox>
          </div>
          <Notice icon={<Lock aria-hidden size={18} />}>
            Un post « Amis uniquement » n'est visible que par vous et vos amis, y compris quand il est publié dans une
            communauté.
          </Notice>
          <Notice tone="danger">Email ou mot de passe incorrect.</Notice>
          <Row label="Liens">
            <TextLink to="/demo">Mot de passe oublié ?</TextLink>
            <TextLink onClick={() => undefined}>Modifier l'email</TextLink>
          </Row>
        </Card>
      </Section>

      <Section title="Contrôles">
        <Card>
          <Row label="Onglets (écran 05b)">
            <Tabs
              aria-label="Amis"
              value={friendsTab}
              onChange={setFriendsTab}
              tabs={[
                { value: 'friends', label: 'Mes amis', count: 86 },
                { value: 'received', label: 'Demandes reçues', count: 2, countTone: 'pending' },
                { value: 'sent', label: 'Demandes envoyées', count: 1 },
              ]}
            />
          </Row>
          <div className={styles.settings}>
            <div className={styles.setting}>
              <div className={styles.settingText}>
                <span className={styles.settingTitle}>Visibilité par défaut de mes posts</span>
                <span className={styles.settingHelp}>
                  Appliquée à chaque nouveau post. Vous pouvez la changer au moment de publier.
                </span>
              </div>
              <SegmentedControl
                aria-label="Visibilité par défaut de mes posts"
                value={visibility}
                onChange={setVisibility}
                segments={[
                  { value: 'public', label: 'Public' },
                  { value: 'friends', label: 'Amis uniquement', icon: <Lock aria-hidden size={14} /> },
                ]}
              />
            </div>
            <div className={styles.setting}>
              <div className={styles.settingText}>
                <span className={styles.settingTitle}>Qui peut voir ma liste d'amis</span>
                <span className={styles.settingHelp}>Sur votre profil public.</span>
              </div>
              <div className={styles.settingSelect}>
                <Select
                  size="sm"
                  aria-label="Qui peut voir ma liste d'amis"
                  defaultValue="friends"
                  options={[
                    { value: 'everyone', label: 'Tout le monde' },
                    { value: 'friends', label: 'Mes amis' },
                    { value: 'me', label: 'Moi uniquement' },
                  ]}
                />
              </div>
            </div>
            <div className={styles.setting}>
              <div className={styles.settingText}>
                <span id="demo-suggestions" className={styles.settingTitle}>
                  Apparaître dans les suggestions d'amis
                </span>
                <span className={styles.settingHelp}>Proposé aux membres de vos communautés.</span>
              </div>
              <Toggle aria-labelledby="demo-suggestions" checked={suggestions} onChange={setSuggestions} />
            </div>
            <div className={styles.setting}>
              <div className={styles.settingText}>
                <span id="demo-notifications" className={styles.settingTitle}>
                  Notifications par email
                </span>
                <span className={styles.settingHelp}>Interrupteur désactivé.</span>
              </div>
              <Toggle aria-labelledby="demo-notifications" checked={notifications} onChange={setNotifications} />
            </div>
          </div>
        </Card>
      </Section>

      <Section title="Cartes, statistiques et listes">
        <Card padding="large">
          <div className={styles.profileHeader}>
            <Avatar name="Camille Martin" size="6xl" />
            <div className={styles.profileIdentity}>
              <span className={styles.profileName}>Camille Martin</span>
              <span className={styles.profileMeta}>@camille · membre depuis 2025 · Marseille</span>
            </div>
            <div className={styles.stats}>
              <StatBlock value={12} label="Sorties" />
              <StatBlock value={34} label="Posts" />
              <StatBlock value={4} label="Communautés" />
              <StatBlock value={1240} label="Amis" />
            </div>
          </div>
        </Card>
        <div className={styles.columns}>
          <Card title="Demandes d'ami reçues">
            <UserRow
              name="Élise Vidal"
              username="elise"
              meta="@elise · 2 communautés en commun · il y a 3 h"
              avatarSize="3xl"
              actions={
                <>
                  <Button size="sm" variant="secondary">
                    Refuser
                  </Button>
                  <Button size="sm">Accepter</Button>
                </>
              }
            />
            <UserRow
              name="Nicolas Bernard"
              username="nico"
              meta="@nico · Écrins & Oisans · hier"
              avatarSize="3xl"
              actions={
                <>
                  <Button size="sm" variant="secondary">
                    Refuser
                  </Button>
                  <Button size="sm">Accepter</Button>
                </>
              }
            />
          </Card>
          <Card title="Suggestions" action={<a className={styles.link} href="#">Tout voir</a>}>
            <UserRow
              name="Hugo Garnier"
              username="hugo"
              meta="Écrins & Oisans · 4 amis en commun"
              actions={
                <Button size="sm" variant="secondary" icon={<UserPlus aria-hidden size={14} />}>
                  Ajouter
                </Button>
              }
            />
            <UserRow
              name="Trail Runner"
              username="trail_runner"
              meta="Propos insultants · 2 signalements"
              compact
              actions={
                <Button size="sm" variant="secondary">
                  Examiner
                </Button>
              }
            />
          </Card>
        </div>
        <Card padding="compact" title="Participants (AvatarGroup)">
          <div className={styles.row}>
            <AvatarGroup names={['Camille Martin', 'Lucas Durand', 'Sarah Blanc']} />
            <span className={styles.participants}>5/8 participants</span>
          </div>
          <div className={styles.row}>
            <AvatarGroup
              size="xl"
              max={8}
              names={['Lucas Durand', 'Sarah Blanc', 'Antoine R', 'Thomas R', 'Julie P', 'Malik K', 'Élise Vidal', 'Nicolas Bernard']}
            />
          </div>
        </Card>
        <div className={styles.statCards}>
          <StatCard label="Utilisateurs" value={2318} note="+142 cette semaine" />
          <StatCard label="Communautés" value={24} note="+1 ce mois-ci" />
          <StatCard label="Sorties actives" value={57} note="12 ce week-end" />
          <StatCard label="Comptes signalés" value={3} note="à traiter" tone="danger" />
        </div>
      </Section>

      <Section title="Communautés et posts">
        <div className={styles.communityCards}>
          <CommunityCard
            community={{ slug: 'ecrins', name: 'Écrins & Oisans', region: 'Alpes', member_count: 1240, post_count: 312, is_member: joined }}
            onToggleMembership={() => setJoined((value) => !value)}
          />
          <CommunityCard
            community={{ slug: 'vercors', name: 'Vercors', region: 'Préalpes', member_count: 540, post_count: 48, is_member: false }}
            onToggleMembership={() => undefined}
          />
          <CommunityCard
            community={{ slug: 'chartreuse', name: 'Chartreuse', region: 'Préalpes', member_count: 1, post_count: 0, is_member: false }}
          />
        </div>
        <PostCard
          post={{
            author: { username: 'lucas', display_name: 'Lucas Durand' },
            body: 'Montée au Glacier Blanc ce matin, conditions parfaites. Je partage le tracé pour ceux qui y vont ce week-end.',
            visibility: 'friends',
            created_at: TWO_HOURS_AGO,
            like_count: liked ? 25 : 24,
            liked,
            can_delete: true,
          }}
          onToggleLike={() => setLiked((value) => !value)}
          onDelete={() => undefined}
          onReport={() => setReporting(true)}
        />
        {/* Envoie un vrai signalement si on valide : à utiliser avec un compte de test. */}
        {reporting && <ReportDialog target={{ username: 'demo' }} label="ce post (démo)" onClose={() => setReporting(false)} />}
        <Card title="Vignettes de publications (PostTile)">
          <div className={styles.communityCards}>
            <PostTile post={{ body: 'Montée au Glacier Blanc ce matin, conditions parfaites.', visibility: 'public', community: null }} />
            <PostTile post={{ body: 'Qui est partant pour le Dôme des Écrins ?', visibility: 'friends', community: null }} />
            <PostTile showBadge={false} post={{ body: 'Coucher de soleil depuis la terrasse.', visibility: 'public', community: null }} />
          </div>
        </Card>
        <Card>
          <div className={styles.fields}>
            <div className={styles.rowBlock}>
              <span className={styles.rowLabel}>Choix segmenté pleine largeur (écran 09)</span>
              <SegmentedControl
                fullWidth
                aria-label="Publier sur"
                value={destination}
                onChange={setDestination}
                segments={[
                  { value: 'profile', label: 'Mon profil' },
                  { value: 'community', label: 'Une communauté' },
                ]}
              />
            </div>
            <ChoiceCards
              aria-label="Visibilité"
              value={visibility}
              onChange={setVisibility}
              choices={[
                { value: 'public', label: 'Public', description: 'Visible par tous les membres', icon: <Globe aria-hidden size={15} /> },
                { value: 'friends', label: 'Amis uniquement', description: 'Visible seulement par vos amis', icon: <Lock aria-hidden size={15} /> },
              ]}
            />
            <Textarea label="Description" placeholder="Racontez votre sortie, les conditions, vos conseils…" />
          </div>
        </Card>
      </Section>

      <Section title="Sorties">
        <div className={styles.communityCards}>
          <OutingCard outing={DEMO_OUTING} />
          <OutingCard outing={{ ...DEMO_OUTING, status: 'full', participant_count: 8, preview: [[44.93, 6.4]] }} viewerUsername="camille" />
          <OutingCard outing={DEMO_OUTING} viewerUsername="camille" compact />
        </div>
        <Card>
          <Row label="Points de stop (sm, md, lg)">
            <StopNumber value={1} size="sm" />
            <StopNumber value={2} />
            <StopNumber value={3} size="lg" />
          </Row>
        </Card>
      </Section>

      <Section title="Barre latérale de modération">
        <div className={styles.sidebarFrame}>
          <ModerationSidebar openReports={3} user={{ name: 'Camille Martin', roleLabel: 'Modération' }} />
        </div>
      </Section>

      <Section title="Couleurs (tokens.ts)">
        <Card>
          <div className={styles.swatches}>
            {Object.entries(colors).map(([name, value]) => (
              <div key={name} className={styles.swatch}>
                <span className={styles.swatchColor} style={{ background: value }} />
                <span className={styles.swatchName}>{name}</span>
                <code className={styles.rowLabel}>{value}</code>
              </div>
            ))}
          </div>
        </Card>
      </Section>
    </div>
  )
}
