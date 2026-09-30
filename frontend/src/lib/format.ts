// « always » : certains navigateurs n'insèrent l'espace qu'à partir de 5 chiffres (« 1240 »).
const numberFormat = new Intl.NumberFormat('fr-FR', { useGrouping: 'always' })

/** 1240 → « 1 240 » (espace fine insécable, comme dans la maquette). */
export function formatNumber(value: number): string {
  return numberFormat.format(value)
}

/** « Camille Martin » → « CM » ; « Élise Vidal » → « EV » (sans accent, comme la maquette). */
export function initials(name: string): string {
  return name
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase() ?? '')
    .join('')
}

/** « Camille Martin » → « Camille M. » (barre de navigation, activité). */
export function shortName(name: string): string {
  const [first, last] = name.trim().split(/\s+/)
  return last ? `${first} ${last[0].toUpperCase()}.` : (first ?? '')
}

const timeFormat = new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit' })
const dayFormat = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short' })

/** « Aujourd'hui à 14:32 », « Hier à 9:05 », « Le 4 oct. à 14:32 ». */
export function formatDayTime(iso: string, now: Date = new Date()): string {
  const date = new Date(iso)
  const time = timeFormat.format(date)
  const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  const days = Math.round((startOfDay(now) - startOfDay(date)) / 86_400_000)
  if (days === 0) return `Aujourd’hui à ${time}`
  if (days === 1) return `Hier à ${time}`
  return `Le ${dayFormat.format(date)} à ${time}`
}

/** Date d'un post : « à l'instant », « il y a 5 min », « il y a 2 h », « hier », « il y a 3 j », « le 4 oct. ». */
export function formatRelative(iso: string, now: Date = new Date()): string {
  const date = new Date(iso)
  const minutes = Math.floor((now.getTime() - date.getTime()) / 60_000)
  if (minutes < 1) return 'à l’instant'
  if (minutes < 60) return `il y a ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `il y a ${hours} h`
  const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  const days = Math.round((startOfDay(now) - startOfDay(date)) / 86_400_000)
  if (days <= 1) return 'hier'
  if (days < 7) return `il y a ${days} j`
  return `le ${dayFormat.format(date)}`
}

const monthYearFormat = new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric' })

/** « mars 2026 » (« Ami depuis mars 2026 »). */
export function formatMonthYear(iso: string): string {
  return monthYearFormat.format(new Date(iso))
}

const numericDateFormat = new Intl.DateTimeFormat('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })

/** « 12/03/2025 » (tableaux de modération). */
export function formatDate(iso: string): string {
  return numericDateFormat.format(new Date(iso))
}

/** « 20 sept. » (« envoyée le 20 sept. »). */
export function formatDay(iso: string): string {
  return dayFormat.format(new Date(iso))
}

/** 1 → « 1 membre », 1240 → « 1 240 membres ». */
export function formatCount(value: number, singular: string, plural = `${singular}s`): string {
  return `${formatNumber(value)} ${value > 1 ? plural : singular}`
}

const weekdayFormat = new Intl.DateTimeFormat('fr-FR', { weekday: 'short' })

/** « Sam. 4 oct. · 7h30 » (date et heure d'une sortie, heure locale). */
export function formatOutingDate(iso: string): string {
  const date = new Date(iso)
  const weekday = weekdayFormat.format(date)
  const time = `${date.getHours()}h${String(date.getMinutes()).padStart(2, '0')}`
  return `${weekday[0].toUpperCase()}${weekday.slice(1)} ${dayFormat.format(date)} · ${time}`
}

/** 9420 → « 9,4 km », 850 → « 850 m ». */
export function formatDistance(meters: number): string {
  if (meters < 1000) return `${formatNumber(Math.round(meters))} m`
  return `${(meters / 1000).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} km`
}

/** 45 → « 0:45 », 75 → « 1:15 ». */
export function formatCountdown(seconds: number): string {
  const safe = Math.max(0, Math.ceil(seconds))
  return `${Math.floor(safe / 60)}:${String(safe % 60).padStart(2, '0')}`
}

/** 2542 → « 2 542 m ». */
export function formatAltitude(meters: number): string {
  return `${formatNumber(meters)} m`
}

/** Texte venu d'une source externe, inséré dans du HTML (icônes Leaflet). */
export function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`)
}
