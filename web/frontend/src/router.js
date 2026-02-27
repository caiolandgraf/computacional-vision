import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('./views/DashboardView.vue'),
    meta: { title: 'Dashboard', icon: '📊' }
  },
  {
    path: '/analyze',
    name: 'AnalyzeImage',
    component: () => import('./views/AnalyzeImageView.vue'),
    meta: { title: 'Analisar Imagem', icon: '🌿' }
  },
  {
    path: '/pothole',
    name: 'PotholeDetection',
    component: () => import('./views/PotholeView.vue'),
    meta: { title: 'Detectar Buracos', icon: '🕳️' }
  },
  {
    path: '/video',
    name: 'VideoProcess',
    component: () => import('./views/VideoProcessView.vue'),
    meta: { title: 'Processar Vídeo', icon: '🎬' }
  },
  {
    path: '/webcam',
    name: 'Webcam',
    component: () => import('./views/WebcamView.vue'),
    meta: { title: 'Webcam Tempo Real', icon: '📹' }
  },
  {
    path: '/batch',
    name: 'BatchAnalysis',
    component: () => import('./views/BatchView.vue'),
    meta: { title: 'Análise em Lote', icon: '📁' }
  },
  {
    path: '/compare',
    name: 'CompareMethods',
    component: () => import('./views/CompareView.vue'),
    meta: { title: 'Comparar Métodos', icon: '🔬' }
  },
  {
    path: '/people',
    name: 'PeopleDetection',
    component: () => import('./views/PeopleDetectionView.vue'),
    meta: { title: 'Detecção de Pessoas', icon: '🧑‍🤝‍🧑' }
  },
  {
    path: '/results',
    name: 'Results',
    component: () => import('./views/ResultsView.vue'),
    meta: { title: 'Resultados', icon: '🗂️' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('./views/SettingsView.vue'),
    meta: { title: 'Configurações', icon: '⚙️' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/'
  }
]

const router = createRouter({
  // Use hash history for GitHub Pages compatibility (no server-side routing)
  // e.g. https://user.github.io/computacional-vision/#/analyze
  history: createWebHashHistory(
    typeof __APP_BASE__ !== 'undefined' ? __APP_BASE__ : '/'
  ),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  }
})

router.beforeEach((to, _from, next) => {
  const title = to.meta?.title || 'Sistema de Detecção'
  document.title = `${title} | Visão Computacional`
  next()
})

export default router

export { routes }
