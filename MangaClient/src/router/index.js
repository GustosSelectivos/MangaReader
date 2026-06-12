import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/features/Catalog/views/HomeView.vue'),
    },
    {
      path: '/library',
      name: 'library',
      component: () => import('@/features/Catalog/views/LibraryView.vue'),
    },
    {
      path: '/reader/:slug',
      name: 'reader',
      component: () => import('@/features/Reader/views/ReaderView.vue'),
      props: true,
    },
    // legacy/alternate route used in templates: keep for backwards compatibility
    {
      path: '/library/manga/:slug',
      name: 'library-manga',
      component: () => import('@/features/Reader/views/ReaderView.vue'),
      props: route => ({ slug: route.params.slug }),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/features/Auth/views/LoginView.vue'),
    },
    {
      path: '/chapter/:chapterId',
      name: 'chapter',
      component: () => import('@/features/Reader/views/ChapterView.vue'),
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
          component: () => import('@/features/Admin/views/AdminDashboardView.vue'),
        },
        {
          path: 'upload',
          name: 'admin-upload',
          component: () => import('@/features/Admin/views/UploadChapterView.vue'),
        },
        {
          path: 'mantenedores',
          name: 'admin-mantenedores',
          component: () => import('@/features/Admin/views/MantenedoresAdminView.vue'),
        },
        {
          path: 'mangas',
          name: 'admin-mangas',
          component: () => import('@/features/Admin/views/MangasAdminView.vue'),
        },
        {
          path: 'profiles',
          name: 'admin-profiles',
          component: () => import('@/features/Admin/views/ProfilesAdminView.vue'),
        },
        {
          path: 'worker',
          name: 'admin-worker',
          component: () => import('@/features/Admin/views/WorkerAdminView.vue'),
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
