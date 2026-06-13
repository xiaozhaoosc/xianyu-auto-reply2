<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between">
      <a-input-search v-model:value="searchText" placeholder="搜索卡券名称" @search="loadData" style="width: 250px" />
      <a-button type="primary" @click="openModal()">新增卡券</a-button>
    </div>

    <a-table :columns="columns" :data-source="dataSource" :loading="loading" :pagination="pagination" @change="handleTableChange" row-key="id">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="record.status === 'ACTIVE' ? 'green' : 'red'">{{ record.status === 'ACTIVE' ? '可用' : '已用' }}</a-tag>
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

    <a-modal v-model:open="modalVisible" :title="editingId ? '编辑卡券' : '新增卡券'" @ok="handleSubmit" :confirm-loading="submitting">
      <a-form :model="form" layout="vertical">
        <a-form-item label="卡券名称" :rules="[{ required: true, message: '请输入名称' }]">
          <a-input v-model:value="form.name" placeholder="请输入卡券名称" />
        </a-form-item>
        <a-form-item label="卡密内容">
          <a-textarea v-model:value="form.content" placeholder="请输入卡密内容" :rows="4" />
        </a-form-item>
        <a-form-item label="关联商品ID">
          <a-input-number v-model:value="form.itemId" placeholder="关联商品ID" style="width: 100%" />
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
import { getCards, createCard, updateCard, deleteCard } from '@/api/card'

const searchText = ref('')
const loading = ref(false)
const dataSource = ref<any[]>([])
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const modalVisible = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const form = reactive({ name: '', content: '', itemId: undefined as number | undefined, remark: '' })

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '关联商品ID', dataIndex: 'itemId', key: 'itemId', width: 100 },
  { title: '备注', dataIndex: 'remark', key: 'remark' },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '操作', key: 'action', width: 160 },
]

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getCards({ page: pagination.current, size: pagination.pageSize, keyword: searchText.value })
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
  form.content = record?.content ?? ''
  form.itemId = record?.itemId ?? undefined
  form.remark = record?.remark ?? ''
  modalVisible.value = true
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    if (editingId.value) {
      await updateCard(editingId.value, form)
      message.success('更新成功')
    } else {
      await createCard(form)
      message.success('创建成功')
    }
    modalVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteCard(id)
  message.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
