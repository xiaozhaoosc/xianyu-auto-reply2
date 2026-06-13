<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between">
      <a-space>
        <a-input-search v-model:value="searchText" placeholder="搜索订单号" @search="loadData" style="width: 250px" />
        <a-select v-model:value="statusFilter" placeholder="订单状态" allowClear style="width: 130px" @change="loadData">
          <a-select-option value="PAID">已付款</a-select-option>
          <a-select-option value="DELIVERED">已发货</a-select-option>
          <a-select-option value="COMPLETED">已完成</a-select-option>
          <a-select-option value="REFUNDED">已退款</a-select-option>
        </a-select>
      </a-space>
      <a-button type="primary" @click="handleSync">同步订单</a-button>
    </div>

    <a-table :columns="columns" :data-source="dataSource" :loading="loading" :pagination="pagination" @change="handleTableChange" row-key="id">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="orderStatusColor(record.status)">{{ orderStatusLabel(record.status) }}</a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button size="small" @click="openDeliveryModal(record)" v-if="record.status === 'PAID'">手动发货</a-button>
            <a-button size="small" @click="viewDetail(record)">详情</a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 手动发货弹窗 -->
    <a-modal v-model:open="deliveryVisible" title="手动发货" @ok="handleDelivery" :confirm-loading="delivering">
      <a-form layout="vertical">
        <a-form-item label="订单号">
          <a-input :value="deliveryForm.orderNo" disabled />
        </a-form-item>
        <a-form-item label="发货内容">
          <a-textarea v-model:value="deliveryForm.content" placeholder="请输入发货内容" :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 订单详情弹窗 -->
    <a-modal v-model:open="detailVisible" title="订单详情" :footer="null" width="600px">
      <a-descriptions :column="1" bordered size="small" v-if="currentOrder">
        <a-descriptions-item label="订单号">{{ currentOrder.orderNo }}</a-descriptions-item>
        <a-descriptions-item label="商品名称">{{ currentOrder.itemTitle }}</a-descriptions-item>
        <a-descriptions-item label="金额">{{ currentOrder.amount }}</a-descriptions-item>
        <a-descriptions-item label="状态">{{ orderStatusLabel(currentOrder.status) }}</a-descriptions-item>
        <a-descriptions-item label="买家">{{ currentOrder.buyerNick }}</a-descriptions-item>
        <a-descriptions-item label="创建时间">{{ currentOrder.createTime }}</a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getOrders, syncOrders, manualDelivery } from '@/api/order'

const searchText = ref('')
const statusFilter = ref<string | undefined>(undefined)
const loading = ref(false)
const dataSource = ref<any[]>([])
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

// 发货弹窗
const deliveryVisible = ref(false)
const delivering = ref(false)
const deliveryForm = reactive({ orderId: null as number | null, orderNo: '', content: '' })

// 详情弹窗
const detailVisible = ref(false)
const currentOrder = ref<any>(null)

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '订单号', dataIndex: 'orderNo', key: 'orderNo', width: 180 },
  { title: '商品', dataIndex: 'itemTitle', key: 'itemTitle', ellipsis: true },
  { title: '金额', dataIndex: 'amount', key: 'amount', width: 80 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 90 },
  { title: '买家', dataIndex: 'buyerNick', key: 'buyerNick', width: 100 },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '操作', key: 'action', width: 160 },
]

const orderStatusColor = (s: string) => ({ PAID: 'blue', DELIVERED: 'green', COMPLETED: 'default', REFUNDED: 'red' }[s] || 'default')
const orderStatusLabel = (s: string) => ({ PAID: '已付款', DELIVERED: '已发货', COMPLETED: '已完成', REFUNDED: '已退款' }[s] || s)

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getOrders({ page: pagination.current, size: pagination.pageSize, keyword: searchText.value, status: statusFilter.value })
    dataSource.value = res.data?.records || res.data?.list || []
    pagination.total = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadData()
}

const handleSync = async () => {
  await syncOrders()
  message.success('同步指令已发送')
  loadData()
}

const openDeliveryModal = (record: any) => {
  deliveryForm.orderId = record.id
  deliveryForm.orderNo = record.orderNo
  deliveryForm.content = ''
  deliveryVisible.value = true
}

const handleDelivery = async () => {
  delivering.value = true
  try {
    await manualDelivery(deliveryForm.orderId!, { content: deliveryForm.content })
    message.success('发货成功')
    deliveryVisible.value = false
    loadData()
  } finally {
    delivering.value = false
  }
}

const viewDetail = (record: any) => {
  currentOrder.value = record
  detailVisible.value = true
}

onMounted(loadData)
</script>
