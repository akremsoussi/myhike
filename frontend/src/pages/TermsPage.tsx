import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router'
import { useAuth } from '../auth/context'
import { Logo } from '../components'
import styles from './TermsPage.module.css'

const SECTIONS = [
  {
    title: '1. Objet',
    paragraphs: [
      'Refuges est un site pour les randonneurs : carte des refuges de montagne, communautés par massif, publications et sorties organisées entre utilisateurs. Ces conditions s’appliquent à toute personne qui crée un compte.',
      'Refuges est un projet scolaire, sans publicité ni service payant.',
    ],
  },
  {
    title: '2. Votre compte',
    paragraphs: [
      'L’inscription demande un nom d’utilisateur, une adresse email valide et un mot de passe d’au moins 8 caractères. Le compte n’est utilisable qu’après confirmation de l’adresse email.',
      'Vous êtes responsable de votre mot de passe. Si vous pensez qu’il a été découvert, changez-le avec « Mot de passe oublié » : toutes vos sessions seront fermées.',
    ],
  },
  {
    title: '3. Ce que vous publiez',
    paragraphs: [
      'Vous restez l’auteur de vos textes, photos et chemins. Vous choisissez pour chaque post sa visibilité : « Public » (tous les membres) ou « Amis uniquement » (vos amis seulement, y compris dans une communauté).',
      'Ne publiez que des contenus que vous avez le droit de partager : pas de propos insultants, de spam, de faux profil, ni de photo d’une personne sans son accord.',
      'La position GPS et les autres métadonnées des photos sont retirées à l’envoi.',
    ],
  },
  {
    title: '4. Sorties en montagne',
    paragraphs: [
      'Les sorties sont organisées entre utilisateurs, sous leur seule responsabilité. Refuges ne vérifie ni les itinéraires, ni le niveau des participants, ni les conditions sur place.',
      'Les distances et dénivelés affichés sont des estimations. Renseignez-vous sur la météo, l’état des refuges et des chemins avant de partir.',
    ],
  },
  {
    title: '5. Modération',
    paragraphs: [
      'Chacun peut signaler un post ou un profil. Les modérateurs peuvent supprimer un contenu, suspendre ou supprimer un compte qui ne respecte pas ces conditions.',
    ],
  },
  {
    title: '6. Données personnelles',
    paragraphs: [
      'Nous conservons votre adresse email (jamais montrée aux autres membres), votre profil, vos publications, vos amitiés et vos sorties. Rien n’est transmis à un service extérieur.',
      'Vos réglages de confidentialité décident qui voit votre liste d’amis, vos sorties à venir et qui peut vous envoyer une demande d’ami. Pour supprimer votre compte, faites-en la demande à un modérateur.',
    ],
  },
  {
    title: '7. Sources',
    paragraphs: [
      'Les informations sur les refuges viennent de refuges.info, sous licence Creative Commons BY-SA 2.0. Le fond de carte vient d’OpenStreetMap (© les contributeurs d’OpenStreetMap, licence ODbL).',
    ],
  },
]

/** Conditions d'utilisation (lien de l'écran 02). Publiques : lisibles avant l'inscription. */
export function TermsPage() {
  const { me } = useAuth()
  const back = me ? { to: '/carte', label: 'Retour au site' } : { to: '/inscription', label: 'Retour à l’inscription' }
  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <Logo to={me ? '/carte' : '/connexion'} />
      </header>
      <main className={styles.page}>
        <Link to={back.to} className={styles.back}>
          <ArrowLeft aria-hidden size={14} />
          {back.label}
        </Link>
        <h1 className={styles.title}>Conditions d’utilisation</h1>
        <p className={styles.updated}>Dernière mise à jour : 10 octobre 2026</p>
        {SECTIONS.map((section) => (
          <section key={section.title} className={styles.section}>
            <h2 className={styles.sectionTitle}>{section.title}</h2>
            {section.paragraphs.map((paragraph) => (
              <p key={paragraph} className={styles.text}>
                {paragraph}
              </p>
            ))}
          </section>
        ))}
      </main>
    </div>
  )
}
