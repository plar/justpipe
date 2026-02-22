import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'pipelines',
    component: () => import('./views/PipelineListView.vue'),
    meta: { title: 'Pipelines' },
  },
  {
    path: '/pipeline/:hash',
    name: 'pipeline-detail',
    component: () => import('./views/PipelineDetailView.vue'),
    meta: { title: 'Pipeline' },
  },
  {
    path: '/run/:id',
    name: 'run-detail',
    component: () => import('./views/RunDetailView.vue'),
    meta: { title: 'Run' },
  },
  {
    path: '/compare',
    name: 'compare',
    component: () => import('./views/CompareView.vue'),
    meta: { title: 'Compare' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: '/',
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  const base = (to.meta.title as string) || 'justpipe'
  if (to.name === 'run-detail' && to.params.id) {
    document.title = `Run ${String(to.params.id).slice(0, 12)} · justpipe`
  } else {
    document.title = `${base} · justpipe`
  }
})
