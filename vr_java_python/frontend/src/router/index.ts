import { createRouter, createWebHistory } from 'vue-router'
import BasicLayout from '@/layouts/BasicLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
  },
  {
    path: '/',
    component: BasicLayout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/dashboard/DashboardView.vue'), meta: { title: '工作台' } },
      { path: 'accounts', name: 'Accounts', component: () => import('@/views/account/AccountList.vue'), meta: { title: '账号管理' } },
      { path: 'cards', name: 'Cards', component: () => import('@/views/card/CardList.vue'), meta: { title: '卡券管理' } },
      { path: 'keyword-rules', name: 'KeywordRules', component: () => import('@/views/rule/KeywordRuleList.vue'), meta: { title: '关键词规则' } },
      { path: 'delivery-rules', name: 'DeliveryRules', component: () => import('@/views/rule/DeliveryRuleList.vue'), meta: { title: '发货规则' } },
      { path: 'default-replies', name: 'DefaultReplies', component: () => import('@/views/rule/DefaultReplyList.vue'), meta: { title: '默认回复' } },
      { path: 'orders', name: 'Orders', component: () => import('@/views/order/OrderList.vue'), meta: { title: '订单管理' } },
      { path: 'products', name: 'Products', component: () => import('@/views/product/ProductList.vue'), meta: { title: '商品管理' } },
      { path: 'materials', name: 'Materials', component: () => import('@/views/product/MaterialList.vue'), meta: { title: '素材库' } },
      { path: 'dock-records', name: 'DockRecords', component: () => import('@/views/dock/DockRecordList.vue'), meta: { title: '分销对接' } },
      { path: 'settings', name: 'Settings', component: () => import('@/views/settings/SettingsView.vue'), meta: { title: '系统设置' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫：未登录跳转登录页
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
