import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LibraryView from '../views/LibraryView.vue'
import ReaderView from '../views/ReaderView.vue'
import ChapterView from '../views/ChapterView.vue'
import LoginView from '../views/LoginView.vue'
import UploadChapterView from '../views/UploadChapterView.vue'
import MantenedoresAdminView from '../views/MantenedoresAdminView.vue'
import MangasAdminView from '../views/MangasAdminView.vue'

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
      component: LibraryView,
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
    // Legacy alias: redirect /uploads to the protected upload screen
    { path: '/uploads', redirect: '/dev/upload' },
    // Protected development/admin routes
    {
      path: '/dev/upload',
      name: 'dev-upload',
      component: UploadChapterView,
      meta: { requiresAuth: true },
    },
    {
      path: '/dev/mantenedores',
      name: 'dev-mantenedores',
      component: MantenedoresAdminView,
      meta: { requiresAuth: true },
    },
    {
      path: '/dev/mangas',
      name: 'dev-mangas',
      component: MangasAdminView,
      meta: { requiresAuth: true },
    },
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
