import { createRouter, createWebHashHistory } from 'vue-router'
  
import AboutView from '../views/AboutView.vue'
import StatsView from '../views/StatsView.vue'
import GenerateView from '../views/GenerateView.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: AboutView
    },
    {
      path: '/view',
      name: 'view',
      component: () => import('../views/ExploreView.vue')
    },
    {
      path: '/stats',
      name: 'stats',
      component: StatsView
    },
    {
      path: '/generate',
      name: 'generate',
      component: GenerateView
    }
  ]
})

export default router
