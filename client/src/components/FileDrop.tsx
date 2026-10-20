import { useState, type DragEvent, type ReactNode } from 'react'
import { ACCEPTED_IMAGE_TYPES } from '../api/media'
import { cx } from '../lib/cx'
import styles from './FileDrop.module.css'

type FileDropProps = {
  /** Fichiers choisis ou déposés (au moins un). */
  onFiles: (files: File[]) => void
  multiple?: boolean
  disabled?: boolean
  /** Nom accessible du champ, quand le contenu n'est pas un texte explicite. */
  'aria-label'?: string
  className?: string
  children: ReactNode
}

/**
 * Zone cliquable où l'on peut aussi glisser une image (« Glisser une image ou parcourir »).
 * Le vrai champ fichier reste dans la page (masqué visuellement) : il prend le focus clavier.
 */
export function FileDrop({ onFiles, multiple = false, disabled = false, className, children, ...rest }: FileDropProps) {
  const [over, setOver] = useState(false)

  function drop(event: DragEvent) {
    event.preventDefault()
    setOver(false)
    if (disabled) return
    const files = [...event.dataTransfer.files]
    if (files.length > 0) onFiles(multiple ? files : files.slice(0, 1))
  }

  return (
    <label
      className={cx(styles.zone, over && styles.over, disabled && styles.disabled, className)}
      onDragOver={(event) => {
        event.preventDefault()
        if (!disabled) setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={drop}
    >
      <input
        type="file"
        className={styles.input}
        accept={ACCEPTED_IMAGE_TYPES.join(',')}
        multiple={multiple}
        disabled={disabled}
        aria-label={rest['aria-label']}
        onChange={(event) => {
          const files = [...(event.target.files ?? [])]
          event.target.value = '' // pouvoir choisir à nouveau le même fichier
          if (files.length > 0) onFiles(files)
        }}
      />
      {children}
    </label>
  )
}
