import { Mountain } from 'lucide-react'
import { Popup } from 'react-leaflet'
import type { RefugeSummary } from '../../api/refuges'
import { ButtonLink } from '../../components'
import styles from './MapPage.module.css'
import { altitudeAndCapacity, guardLabel } from './refugeText'

type RefugePopupProps = {
  refuge: RefugeSummary
  onClose: () => void
}

/** Aperçu du refuge sélectionné, posé sur la carte (écran 03). */
export function RefugePopup({ refuge, onClose }: RefugePopupProps) {
  const meta = [...altitudeAndCapacity(refuge), guardLabel(refuge)].join(' · ')
  return (
    <Popup
      position={[refuge.latitude, refuge.longitude]}
      offset={[0, -14]}
      closeButton={false}
      autoPanPadding={[24, 24]}
      eventHandlers={{ remove: onClose }}
    >
      <div className={styles.popup}>
        {/* Pas encore de photos : zone réservée, comme dans la maquette. */}
        <div className={styles.popupImage} aria-hidden>
          <Mountain size={28} />
        </div>
        {/* <div> et non <p> : Leaflet ajoute de grandes marges aux paragraphes des popups. */}
        <div className={styles.popupName}>{refuge.name}</div>
        {meta && <div className={styles.popupMeta}>{meta}</div>}
        <div className={styles.popupActions}>
          <ButtonLink to={`/refuges/${refuge.id}`} size="sm" fullWidth>
            Voir la fiche
          </ButtonLink>
          <ButtonLink to={`/sorties/nouvelle?refuge=${refuge.id}`} size="sm" variant="secondary" fullWidth>
            Créer une sortie
          </ButtonLink>
        </div>
      </div>
    </Popup>
  )
}
