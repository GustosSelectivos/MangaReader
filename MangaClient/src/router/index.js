import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LibraryView from '../views/LibraryView.vue'
import ReaderView from '../views/ReaderView.vue'
import ChapterView from '../views/ChapterView.vue'
import LoginView from '../views/LoginView.vue'
import UploadChapterView from '../views/UploadChapterView.vue'
import MantenedoresAdminView from '../views/MantenedoresAdminView.vue'
import MangasAdminView from '../views/MangasAdminView.vue'
// MangaCreatorView removed; keep redirect route below

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/library',
      name: 'library',
      redirect: '/', // Library disabled
      // component: LibraryView,
    },
    {
      path: '/reader/:mangaId',
      name: 'reader',
      component: ReaderView,
      props: true,
    },
    // legacy/alternate route used in templates: keep for backwards compatibility
    {
      path: '/library/manga/:mangaId',
      name: 'library-manga',
      component: ReaderView,
      props: route => ({ mangaId: route.params.mangaId }),
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/chapter/:chapterId',
      name: 'chapter',
      component: ChapterView,
      props: true,
    },
    // Legacy alias: redirect /uploads and /dev/uploads etc
    { path: '/uploads', redirect: '/admin/upload' },

    // New Unified Admin Panel
    {
      path: '/admin',
      component: () => import('../layouts/AdminLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'admin-dashboard',
          component: () => import('../views/AdminDashboardView.vue'),
        },
        {
          path: 'upload',
          name: 'admin-upload',
          component: UploadChapterView,
        },
        {
          path: 'mantenedores',
          name: 'admin-mantenedores',
          component: MantenedoresAdminView,
        },
        {
          path: 'mangas',
          name: 'admin-mangas',
          component: MangasAdminView,
        },
        {
          path: 'profiles',
          name: 'admin-profiles',
          component: () => import('../views/ProfilesAdminView.vue'),
        },
        {
          path: 'worker',
          name: 'admin-worker',
          component: () => import('../views/WorkerAdminView.vue'),
        },
      ]
    },

    // Legacy redirects for old dev routes to new admin routes
    { path: '/dev/upload', redirect: { name: 'admin-upload' } },
    { path: '/dev/mantenedores', redirect: { name: 'admin-mantenedores' } },
    { path: '/dev/mangas', redirect: { name: 'admin-mangas' } },
    { path: '/dev/profiles', redirect: { name: 'admin-profiles' } },
    { path: '/dev/manga-creator', redirect: { name: 'admin-mangas' } },
  ],
})

// Simple guard using localStorage token (avoids pinia timing issues)
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      return next({ name: 'login', query: { redirect: to.fullPath } })
    }
  }
  next()
})

export default router
