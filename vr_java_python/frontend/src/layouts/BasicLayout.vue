<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible>
      <div class="logo">{{ collapsed ? '闲鱼' : '闲鱼智能运营平台' }}</div>
      <a-menu theme="dark" v-model:selectedKeys="selectedKeys" @click="onMenuClick">
        <a-menu-item key="dashboard"><DashboardOutlined /> <span>工作台</span></a-menu-item>
        <a-sub-menu key="account-mgmt">
          <template #title><UserOutlined /> <span>账号管理</span></template>
          <a-menu-item key="accounts">闲鱼账号</a-menu-item>
        </a-sub-menu>
        <a-sub-menu key="rule-mgmt">
          <template #title><SettingOutlined /> <span>规则管理</span></template>
          <a-menu-item key="keyword-rules">关键词规则</a-menu-item>
          <a-menu-item key="delivery-rules">发货规则</a-menu-item>
          <a-menu-item key="default-replies">默认回复</a-menu-item>
        </a-sub-menu>
        <a-menu-item key="cards"><CreditCardOutlined /> <span>卡券管理</span></a-menu-item>
        <a-menu-item key="orders"><ShoppingCartOutlined /> <span>订单管理</span></a-menu-item>
        <a-sub-menu key="product-mgmt">
          <template #title><ShopOutlined /> <span>商品管理</span></template>
          <a-menu-item key="products">商品目录</a-menu-item>
          <a-menu-item key="materials">素材库</a-menu-item>
        </a-sub-menu>
        <a-menu-item key="dock-records"><TeamOutlined /> <span>分销对接</span></a-menu-item>
        <a-menu-item key="settings"><ToolOutlined /> <span>系统设置</span></a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header style="background: #fff; padding: 0 24px; display: flex; justify-content: space-between; align-items: center">
        <span style="font-size: 18px; font-weight: 600">{{ currentTitle }}</span>
        <a-button @click="handleLogout">退出登录</a-button>
      </a-layout-header>
      <a-layout-content style="margin: 16px">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { logout } from '@/api/auth'
import {
  DashboardOutlined, UserOutlined, SettingOutlined,
  CreditCardOutlined, ShoppingCartOutlined, ShopOutlined,
  TeamOutlined, ToolOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const selectedKeys = ref([route.name as string])

const currentTitle = computed(() => (route.meta?.title as string) || '闲鱼智能运营平台')

const onMenuClick = ({ key }: { key: string }) => {
  router.push({ name: key })
}

const handleLogout = async () => {
  await logout()
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.logo {
  height: 32px;
  margin: 16px;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  text-align: center;
  line-height: 32px;
  white-space: nowrap;
  overflow: hidden;
}
</style>
