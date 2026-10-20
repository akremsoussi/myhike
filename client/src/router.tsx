import { createBrowserRouter, Navigate } from 'react-router'
import { GuestOnly, RequireActive, RequireModerator, RequirePending } from './auth/guards'
import { AuthLayout } from './layouts/AuthLayout'
import { ModerationLayout } from './layouts/ModerationLayout'
import { UserLayout } from './layouts/UserLayout'
import { CommunitiesPage } from './pages/communities/CommunitiesPage'
import { CommunityMembersPage } from './pages/communities/CommunityMembersPage'
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
import { RefugePostsPage } from './pages/refuges/RefugePostsPage'
import { SearchPage } from './pages/search/SearchPage'
import { ConfirmEmailPage } from './pages/auth/ConfirmEmailPage'
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage'
import { LoginPage } from './pages/auth/LoginPage'
import { PendingPage } from './pages/auth/PendingPage'
import { RegisterPage } from './pages/auth/RegisterPage'
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage'
import { DemoPage } from './pages/DemoPage'
import { EditProfilePage } from './pages/profile/EditProfilePage'
import { FriendsPage } from './pages/profile/FriendsPage'
import { ProfilePage } from './pages/profile/ProfilePage'
import { UserProfilePage } from './pages/profile/UserProfilePage'
import { PrivacySettingsPage } from './pages/settings/PrivacySettingsPage'
import { StatusPage } from './pages/StatusPage'
import { TermsPage } from './pages/TermsPage'

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/carte" replace /> },
  { path: '/statut', element: <StatusPage /> },
  // Publiques, connecté ou non : lisibles avant l'inscription.
  { path: '/conditions', element: <TermsPage /> },
  {
    element: <AuthLayout />,
    children: [
      {
        element: <GuestOnly />,
        children: [
          { path: '/connexion', element: <LoginPage /> },
          { path: '/inscription', element: <RegisterPage /> },
          { path: '/mot-de-passe-oublie', element: <ForgotPasswordPage /> },
        ],
      },
      {
        element: <RequirePending />,
        children: [{ path: '/inscription/confirmation', element: <PendingPage /> }],
      },
      { path: '/inscription/confirmer', element: <ConfirmEmailPage /> },
      // Lien reçu par email : il peut s'ouvrir dans un navigateur déjà connecté.
      { path: '/mot-de-passe/nouveau', element: <ResetPasswordPage /> },
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
          { path: '/refuges/:id/posts', element: <RefugePostsPage /> },
          { path: '/sorties/nouvelle', element: <OutingFormPage /> },
          { path: '/sorties/:id', element: <OutingPage /> },
          { path: '/sorties/:id/modifier', element: <OutingFormPage /> },
          { path: '/communautes', element: <CommunitiesPage /> },
          { path: '/communautes/:slug/membres', element: <CommunityMembersPage /> },
          { path: '/posts/nouveau', element: <NewPostPage /> },
          { path: '/sorties', element: <OutingsPage /> },
          { path: '/profil', element: <ProfilePage /> },
          { path: '/profil/amis', element: <FriendsPage /> },
          { path: '/profil/modifier', element: <EditProfilePage /> },
          { path: '/parametres/confidentialite', element: <PrivacySettingsPage /> },
          { path: '/u/:username', element: <UserProfilePage /> },
          { path: '/recherche', element: <SearchPage /> },
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
