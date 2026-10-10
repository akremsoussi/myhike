import { ArrowLeft, Plus } from 'lucide-react'
import { Link, useParams } from 'react-router'
import { refugesApi } from '../../api/refuges'
import { ButtonLink, Card, Notice, Tag } from '../../components'
import { formatAltitude } from '../../lib/format'
import { useApi } from '../../lib/useApi'
import { guardLabel, isClosed } from '../map/refugeText'
import { PostFeed } from '../posts/PostFeed'
import styles from './RefugePostsPage.module.css'

/** « Voir les posts liés » de la fiche refuge : posts rattachés au refuge, selon leur visibilité. */
export function RefugePostsPage() {
  const { id = '' } = useParams()
  const refugeId = Number(id)
  const { data: refuge, error, errorCode } = useApi(`refuge:${id}`, () => refugesApi.get(refugeId), 'Le refuge n’a pas pu être chargé.')

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

  const newPostUrl = `/posts/nouveau?refuge=${refuge.id}`
  return (
    <div className={styles.page}>
      <nav className={styles.breadcrumb} aria-label="Fil d’Ariane">
        <Link to="/carte" className={styles.crumbLink}>
          <ArrowLeft aria-hidden size={14} />
          Carte
        </Link>
        <span aria-hidden>/</span>
        <Link to={`/refuges/${refuge.id}`} className={styles.crumbLink}>
          {refuge.name}
        </Link>
        <span aria-hidden>/</span>
        <span aria-current="page">Posts liés</span>
      </nav>
      <h1 className={styles.title}>Posts liés à {refuge.name}</h1>

      <div className={styles.columns}>
        <PostFeed key={refuge.id} load={(before) => refugesApi.posts(refuge.id, before)} hideRefuge empty="Personne n’a encore publié sur ce refuge." />

        <aside className={styles.aside}>
          <Card>
            <h2 className={styles.name}>{refuge.name}</h2>
            <div className={styles.tags}>
              <Tag tone={refuge.is_guarded && !isClosed(refuge) ? 'filled' : 'outline'}>{guardLabel(refuge)}</Tag>
              {refuge.altitude !== null && <Tag>{formatAltitude(refuge.altitude)}</Tag>}
              {refuge.massif && <Tag>{refuge.massif.name}</Tag>}
            </div>
            <ButtonLink to={newPostUrl} fullWidth icon={<Plus aria-hidden size={16} />}>
              Publier sur ce refuge
            </ButtonLink>
            <ButtonLink to={`/refuges/${refuge.id}`} variant="secondary" fullWidth>
              Voir la fiche
            </ButtonLink>
          </Card>
          <p className={styles.help}>
            Seuls les posts que vous pouvez voir apparaissent ici : les posts « Amis uniquement » restent réservés aux amis
            de leur auteur.
          </p>
        </aside>
      </div>
    </div>
  )
}
