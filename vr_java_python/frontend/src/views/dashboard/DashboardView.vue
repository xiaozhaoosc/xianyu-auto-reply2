<template>
  <div>
    <a-row :gutter="16">
      <a-col :span="6" v-for="item in stats" :key="item.title">
        <a-card>
          <a-statistic :title="item.title" :value="item.value" :suffix="item.suffix">
            <template #prefix>
              <component :is="item.icon" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>
    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="12">
        <a-card title="最近订单">
          <a-empty v-if="recentOrders.length === 0" description="暂无数据" />
          <a-list :data-source="recentOrders" v-else size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :title="item.orderNo" :description="item.status" />
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="账号状态">
          <a-empty v-if="accountStats.length === 0" description="暂无数据" />
          <a-list :data-source="accountStats" v-else size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :title="item.nickname" :description="item.status" />
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { UserOutlined, ShoppingCartOutlined, CreditCardOutlined, TeamOutlined } from '@ant-design/icons-vue'

// 统计卡片数据
const stats = ref([
  { title: '在线账号', value: 0, suffix: '个', icon: UserOutlined },
  { title: '今日订单', value: 0, suffix: '单', icon: ShoppingCartOutlined },
  { title: '可用卡券', value: 0, suffix: '张', icon: CreditCardOutlined },
  { title: '分销渠道', value: 0, suffix: '个', icon: TeamOutlined },
])

const recentOrders = ref<any[]>([])
const accountStats = ref<any[]>([])
</script>
