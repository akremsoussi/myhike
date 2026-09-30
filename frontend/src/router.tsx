import { createBrowserRouter, Navigate } from 'react-router'
import { GuestOnly, RequireActive, RequireModerator, RequirePending } from './auth/guards'
import { AuthLayout } from './layouts/AuthLayout'
import { ModerationLayout } from './layouts/ModerationLayout'
import { UserLayout } from './layouts/UserLayout'
import { CommunitiesPage } from './pages/communities/CommunitiesPage'
import { CommunityPage } from './pages/communities/CommunityPage'
import { AccountsPage } from './pages/moderation/AccountsPage'
import { CommunitiesAdminPage } from './pages/moderation/CommunitiesAdminPage'
import { CommunityFormPage } from './pages/moderation/CommunityFormPage'
import { DashboardPage } from './pages/moderation/DashboardPage'
import { ReportsPage } from './pages/moderation/ReportsPage'
import { NewPostPage } from './pages/posts/NewPostPage'
import { OutingFormPage } from './pages/outings/OutingFormPage'
import { OutingPage } from './pages/outings/OutingPage'
import { OutingsPage } from './pages/outings/OutingsPage'
import { RefugePage } from './pages/refuges/RefugePage'
import { AuthPlaceholderPage } from './pages/auth/AuthPlaceholderPage'
import { ConfirmEmailPage } from './pages/auth/ConfirmEmailPage'
import { LoginPage } from './pages/auth/LoginPage'
import { PendingPage } from './pages/auth/PendingPage'
import { RegisterPage } from './pages/auth/RegisterPage'
import { DemoPage } from './pages/DemoPage'
import { FriendsPage } from './pages/profile/FriendsPage'
import { ProfilePage } from './pages/profile/ProfilePage'
import { UserProfilePage } from './pages/profile/UserProfilePage'
import { PrivacySettingsPage } from './pages/settings/PrivacySettingsPage'
import { StatusPage } from './pages/StatusPage'

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/carte" replace /> },
  { path: '/statut', element: <StatusPage /> },
  {
    element: <AuthLayout />,
    children: [
      {
        element: <GuestOnly />,
        children: [
          { path: '/connexion', element: <LoginPage /> },
          { path: '/inscription', element: <RegisterPage /> },
        ],
      },
      {
        element: <RequirePending />,
        children: [{ path: '/inscription/confirmation', element: <PendingPage /> }],
      },
      { path: '/inscription/confirmer', element: <ConfirmEmailPage /> },
      { path: '/mot-de-passe-oublie', element: <AuthPlaceholderPage title="Mot de passe oublié" /> },
      { path: '/conditions', element: <AuthPlaceholderPage title="Conditions d'utilisation" /> },
    ],
  },
  {
    element: <RequireActive />,
    children: [
      {
        element: <UserLayout fullBleed />,
        // Leaflet n'est chargé qu'en ouvrant la carte.
        children: [{ path: '/carte', lazy: async () => ({ Component: (await import('./pages/map/MapPage')).MapPage }) }],
      },
      {
        element: <UserLayout edgeToEdge />,
        children: [{ path: '/communautes/:slug', element: <CommunityPage /> }],
      },
      {
        element: <UserLayout />,
        children: [
          { path: '/demo', element: <DemoPage /> },
          { path: '/refuges/:id', element: <RefugePage /> },
          { path: '/sorties/nouvelle', element: <OutingFormPage /> },
          { path: '/sorties/:id', element: <OutingPage /> },
          { path: '/sorties/:id/modifier', element: <OutingFormPage /> },
          { path: '/communautes', element: <CommunitiesPage /> },
          { path: '/posts/nouveau', element: <NewPostPage /> },
          { path: '/sorties', element: <OutingsPage /> },
          { path: '/profil', element: <ProfilePage /> },
          { path: '/profil/amis', element: <FriendsPage /> },
          { path: '/parametres/confidentialite', element: <PrivacySettingsPage /> },
          { path: '/u/:username', element: <UserProfilePage /> },
        ],
      },
      {
        element: <RequireModerator />,
        children: [
          {
            path: '/moderation',
            element: <ModerationLayout />,
            children: [
              { index: true, element: <DashboardPage /> },
              { path: 'communautes', element: <CommunitiesAdminPage /> },
              { path: 'communautes/:slug', element: <CommunityFormPage /> },
              { path: 'comptes', element: <AccountsPage /> },
              { path: 'signalements', element: <ReportsPage /> },
            ],
          },
        ],
      },
    ],
  },
])
