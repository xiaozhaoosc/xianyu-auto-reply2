<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between">
      <a-input-search v-model:value="searchText" placeholder="搜索分销渠道" @search="loadData" style="width: 250px" />
      <a-button type="primary" @click="openModal()">新增对接</a-button>
    </div>

    <a-table :columns="columns" :data-source="dataSource" :loading="loading" :pagination="pagination" @change="handleTableChange" row-key="id">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="record.status === 'ACTIVE' ? 'green' : 'red'">{{ record.status === 'ACTIVE' ? '启用' : '停用' }}</a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button size="small" type="primary" @click="openModal(record)">编辑</a-button>
            <a-popconfirm title="确定删除？" @confirm="handleDelete(record.id)">
              <a-button size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal v-model:open="modalVisible" :title="editingId ? '编辑分销对接' : '新增分销对接'" @ok="handleSubmit" :confirm-loading="submitting" width="600px">
      <a-form :model="form" layout="vertical">
        <a-form-item label="渠道名称" :rules="[{ required: true, message: '请输入渠道名称' }]">
          <a-input v-model:value="form.name" placeholder="分销渠道名称" />
        </a-form-item>
        <a-form-item label="回调URL">
          <a-input v-model:value="form.callbackUrl" placeholder="订单回调通知URL" />
        </a-form-item>
        <a-form-item label="密钥">
          <a-input v-model:value="form.secretKey" placeholder="签名密钥" />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="form.status">
            <a-select-option value="ACTIVE">启用</a-select-option>
            <a-select-option value="INACTIVE">停用</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="备注">
          <a-input v-model:value="form.remark" placeholder="备注" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const getDockRecords = (params: any) => request.get('/dock-records', { params })
const createDockRecord = (data: any) => request.post('/dock-records', data)
const updateDockRecord = (id: number, data: any) => request.put(`/dock-records/${id}`, data)
const deleteDockRecord = (id: number) => request.delete(`/dock-records/${id}`)

const searchText = ref('')
const loading = ref(false)
const dataSource = ref<any[]>([])
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const modalVisible = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const form = reactive({ name: '', callbackUrl: '', secretKey: '', status: 'ACTIVE', remark: '' })

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '渠道名称', dataIndex: 'name', key: 'name' },
  { title: '回调URL', dataIndex: 'callbackUrl', key: 'callbackUrl', ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '备注', dataIndex: 'remark', key: 'remark', ellipsis: true },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '操作', key: 'action', width: 160 },
]

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getDockRecords({ page: pagination.current, size: pagination.pageSize, keyword: searchText.value })
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
  form.name = record?.name ?? ''
  form.callbackUrl = record?.callbackUrl ?? ''
  form.secretKey = record?.secretKey ?? ''
  form.status = record?.status ?? 'ACTIVE'
  form.remark = record?.remark ?? ''
  modalVisible.value = true
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    if (editingId.value) {
      await updateDockRecord(editingId.value, form)
      message.success('更新成功')
    } else {
      await createDockRecord(form)
      message.success('创建成功')
    }
    modalVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteDockRecord(id)
  message.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
