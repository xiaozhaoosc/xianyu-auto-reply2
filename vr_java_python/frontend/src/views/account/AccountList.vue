<template>
  <div>
    <!-- 搜索栏 -->
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between">
      <a-space>
        <a-input-search v-model:value="searchText" placeholder="搜索账号昵称" @search="loadData" style="width: 250px" />
        <a-select v-model:value="statusFilter" placeholder="状态筛选" allowClear style="width: 120px" @change="loadData">
          <a-select-option value="ONLINE">在线</a-select-option>
          <a-select-option value="OFFLINE">离线</a-select-option>
          <a-select-option value="EXPIRED">Cookie过期</a-select-option>
        </a-select>
      </a-space>
      <a-button type="primary" @click="openModal()">新增账号</a-button>
    </div>

    <!-- 账号列表 -->
    <a-table :columns="columns" :data-source="dataSource" :loading="loading" :pagination="pagination" @change="handleTableChange" row-key="id">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button size="small" @click="handleLoginAccount(record)">登录</a-button>
            <a-button size="small" @click="handleRefreshCookie(record)">刷新Cookie</a-button>
            <a-button size="small" type="primary" @click="openModal(record)">编辑</a-button>
            <a-popconfirm title="确定删除？" @confirm="handleDelete(record.id)">
              <a-button size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 新增/编辑弹窗 -->
    <a-modal v-model:open="modalVisible" :title="editingId ? '编辑账号' : '新增账号'" @ok="handleSubmit" :confirm-loading="submitting">
      <a-form :model="form" layout="vertical">
        <a-form-item label="账号昵称" :rules="[{ required: true, message: '请输入昵称' }]">
          <a-input v-model:value="form.nickname" placeholder="请输入闲鱼账号昵称" />
        </a-form-item>
        <a-form-item label="Cookie">
          <a-textarea v-model:value="form.cookie" placeholder="请粘贴闲鱼Cookie" :rows="4" />
        </a-form-item>
        <a-form-item label="备注">
          <a-input v-model:value="form.remark" placeholder="备注信息" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getAccounts, createAccount, updateAccount, deleteAccount, loginAccount, refreshCookie } from '@/api/account'

const searchText = ref('')
const statusFilter = ref<string | undefined>(undefined)
const loading = ref(false)
const dataSource = ref<any[]>([])
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

// 弹窗状态
const modalVisible = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const form = reactive({ nickname: '', cookie: '', remark: '' })

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '昵称', dataIndex: 'nickname', key: 'nickname' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '备注', dataIndex: 'remark', key: 'remark' },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '操作', key: 'action', width: 320 },
]

const statusColor = (status: string) => ({ ONLINE: 'green', OFFLINE: 'default', EXPIRED: 'red' }[status] || 'default')
const statusLabel = (status: string) => ({ ONLINE: '在线', OFFLINE: '离线', EXPIRED: 'Cookie过期' }[status] || status)

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getAccounts({ page: pagination.current, size: pagination.pageSize, keyword: searchText.value, status: statusFilter.value })
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

const openModal = (record?: any) => {
  editingId.value = record?.id ?? null
  form.nickname = record?.nickname ?? ''
  form.cookie = record?.cookie ?? ''
  form.remark = record?.remark ?? ''
  modalVisible.value = true
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    if (editingId.value) {
      await updateAccount(editingId.value, form)
      message.success('更新成功')
    } else {
      await createAccount(form)
      message.success('创建成功')
    }
    modalVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteAccount(id)
  message.success('删除成功')
  loadData()
}

const handleLoginAccount = async (record: any) => {
  await loginAccount(record.id)
  message.success('登录指令已发送')
}

const handleRefreshCookie = async (record: any) => {
  await refreshCookie(record.id)
  message.success('Cookie刷新指令已发送')
}

onMounted(loadData)
</script>
