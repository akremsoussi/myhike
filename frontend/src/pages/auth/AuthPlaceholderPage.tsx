import { Notice, TextLink } from '../../components'
import styles from './AuthForm.module.css'

/** Écran référencé par la maquette mais pas encore dessiné. */
export function AuthPlaceholderPage({ title }: { title: string }) {
  return (
    <div className={styles.form}>
      <h1 className={styles.title}>{title}</h1>
      <Notice>Cet écran reste à concevoir.</Notice>
      <TextLink to="/connexion">← Retour à la connexion</TextLink>
    </div>
  )
}
