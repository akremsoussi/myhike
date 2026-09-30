/**
 * Refuges — design tokens côté JS/TS.
 * Mêmes valeurs que tokens.css (générés depuis la même source).
 * À utiliser là où le CSS ne suffit pas : carte (tracé, marqueurs), canvas, graphiques.
 * Pour le style des composants, préférer var(--…) dans le CSS.
 */

export const colors = {
  // Marque
  primary: "#21664a",
  primarySoft: "#deede3",
  primarySubtle: "#f1f7f3",
  onPrimary: "#ffffff",
  // Barre latérale de modération
  sidebarBg: "#174a36",
  sidebarText: "#c7ded1",
  sidebarIcon: "#8cb29e",
  // Neutres
  bg: "#f6f6f2",
  surface: "#ffffff",
  border: "#dee0db",
  neutralBadge: "#dee0db",
  text: "#1a1f1c",
  textMuted: "#707873",
  // Danger
  danger: "#c2302b",
  dangerSoft: "#fce8e5",
  dangerBorder: "#edb8b2",
  // Accent orange (chemins et statuts)
  accent: "#d9731f",
  accentSoft: "#fceddb",
  // En attente (amis, confirmation du compte)
  pending: "#b5530f",
  pendingSoft: "#fbe9d8",
  // Carte et placeholders d'images
  mapBg: "#d4e3cc",
  mapRelief: "#bfd9b8",
  mapWater: "#b2d4eb",
  placeholderPath: "#f2e0cc",
  // Superposition
  overlay: "rgba(26, 31, 28, 0.72)",
} as const;

export const font = {
  family: '"Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  weight: { regular: 400, medium: 500, semibold: 600, bold: 700 },
  size: {
    "3xs": 10,
    "2xs": 11,
    "xs": 12,
    "sm": 13,
    "md": 14,
    "base": 15,
    "lg": 16,
    "xl": 17,
    "2xl": 18,
    "3xl": 20,
    "4xl": 22,
    "5xl": 24,
    "6xl": 28,
    "7xl": 30,
    "8xl": 32,
    "9xl": 34,
    "display": 46,
  },
  lineHeight: { normal: "normal", relaxed: 1.45 },
} as const;

export const space = {
  "0.5": 2,
  "1": 4,
  "1.5": 6,
  "2": 8,
  "2.5": 10,
  "3": 12,
  "3.5": 14,
  "4": 16,
  "5": 20,
  "6": 24,
  "7": 28,
  "8": 32,
  "10": 40,
  "16": 64,
  "20": 80,
} as const;

export const radius = {
  xs: 4,
  sm: 8,
  md: 10,
  lg: 12,
  xl: 14,
  full: 999,
} as const;

export const borderWidth = { default: 1, button: 1.5 } as const;

export const shadow = {
  mapPin: "0 4px 14px rgba(0, 0, 0, 0.16)",
  mapMarker: "0 3px 10px rgba(0, 0, 0, 0.16)",
} as const;

export const avatar = {
  "xs": 24,
  "sm": 30,
  "md": 32,
  "lg": 34,
  "xl": 36,
  "2xl": 40,
  "3xl": 44,
  "4xl": 64,
  "5xl": 72,
  "6xl": 96,
} as const;

export const layout = {
  navbarHeight: 69,
  pageMaxWidth: 1200,
  pagePaddingX: 120,
  pagePaddingY: 28,
  pageNarrowMaxWidth: 1040,
  columnGap: 24,
  authVisualWidth: 800,
  authFormWidth: 420,
  sidebarWidth: 260,
  settingsMenuWidth: 260,
} as const;

export const tokens = { colors, font, space, radius, borderWidth, shadow, avatar, layout } as const;
export type Tokens = typeof tokens;
export default tokens;
