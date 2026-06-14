import { createRouter, createWebHistory } from 'vue-router'

import DashboardView from '../views/DashboardView.vue'
import InventoryView from '../views/InventoryView.vue'
import OrdersView from '../views/OrdersView.vue'
import RecordsView from '../views/RecordsView.vue'
import SuppliersView from '../views/SuppliersView.vue'

const routes = [
  { path: '/', name: 'dashboard', component: DashboardView },
  { path: '/inventory', name: 'inventory', component: InventoryView },
  { path: '/orders', name: 'orders', component: OrdersView },
  { path: '/suppliers', name: 'suppliers', component: SuppliersView },
  { path: '/records', name: 'records', component: RecordsView }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
