import { useEffect, useRef, useState, type FormEvent } from 'react'
import { REPORT_REASONS, reportsApi, type ReportReason } from '../api/moderation'
import { ApiError } from '../lib/api'
import { Button } from './Button'
import { Notice } from './Notice'
import styles from './ReportDialog.module.css'
import { Select } from './Select'
import { Textarea } from './Textarea'

type ReportDialogProps = {
  /** Ce qu'on signale : un post ou un compte. */
  target: { post_id: number } | { username: string }
  /** « ce post », « le compte de Lucas »… */
  label: string
  onClose: () => void
}

/** Fenêtre « Signaler » (pas d'écran dans la maquette) : motif et précision facultative. */
export function ReportDialog({ target, label, onClose }: ReportDialogProps) {
  const ref = useRef<HTMLDialogElement>(null)
  const [reason, setReason] = useState<ReportReason>('insulting')
  const [comment, setComment] = useState('')
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Pas de close() au démontage : il déclencherait onClose (deux fois en StrictMode).
  // Retirer l'élément du DOM suffit à fermer la fenêtre.
  useEffect(() => {
    const dialog = ref.current
    if (dialog && !dialog.open) dialog.showModal()
  }, [])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setSending(true)
    setError(null)
    try {
      await reportsApi.create({ ...target, reason, comment })
      setSent(true)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Le signalement n’a pas pu être envoyé.')
    } finally {
      setSending(false)
    }
  }

  return (
    <dialog ref={ref} className={styles.dialog} onClose={onClose} aria-labelledby="report-title">
      <form className={styles.form} onSubmit={(event) => void submit(event)}>
        <h2 id="report-title" className={styles.title}>
          Signaler {label}
        </h2>
        {sent ? (
          <>
            <Notice>Merci, l’équipe de modération va examiner ce signalement.</Notice>
            <div className={styles.actions}>
              <Button onClick={onClose}>Fermer</Button>
            </div>
          </>
        ) : (
          <>
            <Select
              label="Motif"
              value={reason}
              onChange={(event) => setReason(event.target.value as ReportReason)}
              options={Object.entries(REPORT_REASONS).map(([value, text]) => ({ value, label: text }))}
            />
            <Textarea
              label="Précisions (facultatif)"
              value={comment}
              maxLength={500}
              className={styles.comment}
              onChange={(event) => setComment(event.target.value)}
            />
            {error && <Notice tone="danger">{error}</Notice>}
            <div className={styles.actions}>
              <Button variant="secondary" onClick={onClose}>
                Annuler
              </Button>
              <Button type="submit" disabled={sending}>
                {sending ? 'Envoi…' : 'Signaler'}
              </Button>
            </div>
          </>
        )}
      </form>
    </dialog>
  )
}
