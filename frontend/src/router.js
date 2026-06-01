import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Admin from './views/Admin.vue'
import BlacklistView from './views/BlacklistView.vue'
import DomesticView from './views/DomesticView.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/admin', component: Admin },
  { path: '/blacklist', component: BlacklistView },
  { path: '/domestic', component: DomesticView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
