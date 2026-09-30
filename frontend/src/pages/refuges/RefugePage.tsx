import { ArrowLeft, ChevronRight } from 'lucide-react'
import { lazy, Suspense, type ReactNode } from 'react'
import { Link, useParams } from 'react-router'
import { outingsApi } from '../../api/outings'
import { refugesApi, type RefugeDetail, type RefugeKind } from '../../api/refuges'
import { Button, ButtonLink, Card, Notice, Tag } from '../../components'
import { formatAltitude, formatNumber, formatOutingDate } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import { guardLabel, isClosed } from '../map/refugeText'
import styles from './RefugePage.module.css'

// Leaflet n'est chargé que pour afficher la carte d'accès.
const RefugeMiniMap = lazy(async () => ({ default: (await import('./RefugeMiniMap')).RefugeMiniMap }))

const KIND_LABELS: Record<RefugeKind, string> = {
  guarded_hut: 'Refuge gardé',
  gite: 'Gîte d’étape',
  unguarded_hut: 'Cabane non gardée',
}

const dateFormat = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })

function InfoRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className={styles.infoRow}>
      <dt className={styles.infoLabel}>{label}</dt>
      <dd className={styles.infoValue}>{children}</dd>
    </div>
  )
}

/** Écran 04 · Fiche refuge. */
export function RefugePage() {
  const { id = '' } = useParams()
  const refugeId = Number(id)
  const { data: refuge, error, errorCode } = useApi(
    `refuge:${id}`,
    () => refugesApi.get(refugeId),
    'Le refuge n’a pas pu être chargé.',
  )
  const outings = useApi(
    `refuge-outings:${id}`,
    () => outingsApi.list('upcoming', refugeId),
    'Les sorties n’ont pas pu être chargées.',
  )

  if (errorCode === 'not_found' || !Number.isInteger(refugeId)) {
    return (
      <div className={styles.page}>
        <Notice tone="danger">Ce refuge n’existe pas.</Notice>
        <Link to="/carte" className={styles.crumbLink}>
          ← Retour à la carte
        </Link>
      </div>
    )
  }
  if (!refuge) return <div className={styles.page}>{error && <Notice tone="danger">{error}</Notice>}</div>

  return (
    <div className={styles.page}>
      <nav className={styles.breadcrumb} aria-label="Fil d’Ariane">
        <Link to="/carte" className={styles.crumbLink}>
          <ArrowLeft aria-hidden size={14} />
          Carte
        </Link>
        {refuge.massif && (
          <>
            <span aria-hidden>/</span>
            <span>{refuge.massif.name}</span>
          </>
        )}
        <span aria-hidden>/</span>
        <span aria-current="page">{refuge.name}</span>
      </nav>

      <div className={styles.columns}>
        <div className={styles.main}>
          {/* Pas encore de photos : zone réservée, comme dans la maquette. */}
          <div className={styles.photo}>Photo du refuge</div>

          <Card title="Description">
            <p className={styles.text}>{refuge.remarks ?? 'Pas encore de description.'}</p>
          </Card>

          <Card title="Accès">
            <Suspense fallback={<div className={styles.miniMap} />}>
              <RefugeMiniMap latitude={refuge.latitude} longitude={refuge.longitude} name={refuge.name} />
            </Suspense>
            <p className={styles.text}>{refuge.access ?? 'Pas d’indication d’accès.'}</p>
          </Card>

          <Source refuge={refuge} />
        </div>

        <aside className={styles.aside}>
          <Card>
            <h1 className={styles.name}>{refuge.name}</h1>
            <div className={styles.tags}>
              <Tag tone={refuge.is_guarded && !isClosed(refuge) ? 'filled' : 'outline'}>{guardLabel(refuge)}</Tag>
              {refuge.altitude !== null && <Tag>{formatAltitude(refuge.altitude)}</Tag>}
              {refuge.capacity !== null && <Tag>{formatNumber(refuge.capacity)} places</Tag>}
            </div>
            <dl className={styles.info}>
              {refuge.massif && <InfoRow label="Massif">{refuge.massif.name}</InfoRow>}
              <InfoRow label="Type">{KIND_LABELS[refuge.kind]}</InfoRow>
              {refuge.state && <InfoRow label="État">{refuge.state}</InfoRow>}
              {refuge.phone && (
                <InfoRow label="Téléphone">
                  <a href={`tel:${refuge.phone.replaceAll(' ', '')}`} className={styles.phone}>
                    {refuge.phone}
                  </a>
                </InfoRow>
              )}
            </dl>
            <ButtonLink to={`/sorties/nouvelle?refuge=${refuge.id}`} fullWidth>
              Créer une sortie ici
            </ButtonLink>
            {/* Écran des posts liés à un refuge : pas encore dessiné. */}
            <Button variant="secondary" fullWidth disabled title="Bientôt disponible">
              Voir les posts liés
            </Button>
          </Card>

          <Card title="Sorties prévues ici">
            {outings.data?.length === 0 && <p className={styles.muted}>Aucune sortie prévue pour l’instant.</p>}
            {outings.data?.map((outing) => (
              <Link key={outing.id} to={`/sorties/${outing.id}`} className={styles.outing}>
                <span className={styles.outingText}>
                  <span className={styles.outingTitle}>{outing.title}</span>
                  <span className={styles.outingMeta}>
                    {formatOutingDate(outing.starts_at).split(' · ')[0]} · {outing.participant_count}/
                    {outing.max_participants}
                  </span>
                </span>
                <ChevronRight aria-hidden size={18} className={styles.chevron} />
              </Link>
            ))}
          </Card>
        </aside>
      </div>
    </div>
  )
}

/** Attribution obligatoire (licence CC BY-SA 2.0 de refuges.info). */
function Source({ refuge }: { refuge: RefugeDetail }) {
  return (
    <p className={styles.source}>
      Informations :{' '}
      {refuge.source_url ? (
        <a href={refuge.source_url} target="_blank" rel="noreferrer">
          fiche refuges.info
        </a>
      ) : (
        'refuges.info'
      )}{' '}
      (licence{' '}
      <a href="https://creativecommons.org/licenses/by-sa/2.0/deed.fr" target="_blank" rel="noreferrer">
        CC BY-SA 2.0
      </a>
      ){refuge.source_updated_at && `, mise à jour le ${dateFormat.format(new Date(refuge.source_updated_at))}`}.
    </p>
  )
}
