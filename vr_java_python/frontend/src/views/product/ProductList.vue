<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between">
      <a-input-search v-model:value="searchText" placeholder="搜索商品名称" @search="loadData" style="width: 250px" />
      <a-button type="primary" @click="openModal()">新增商品</a-button>
    </div>

    <a-table :columns="columns" :data-source="dataSource" :loading="loading" :pagination="pagination" @change="handleTableChange" row-key="id">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="record.status === 'ON_SALE' ? 'green' : 'default'">{{ record.status === 'ON_SALE' ? '在售' : '下架' }}</a-tag>
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

    <a-modal v-model:open="modalVisible" :title="editingId ? '编辑商品' : '新增商品'" @ok="handleSubmit" :confirm-loading="submitting" width="600px">
      <a-form :model="form" layout="vertical">
        <a-form-item label="商品名称" :rules="[{ required: true, message: '请输入商品名称' }]">
          <a-input v-model:value="form.title" placeholder="请输入商品名称" />
        </a-form-item>
        <a-form-item label="闲鱼商品ID">
          <a-input v-model:value="form.itemId" placeholder="闲鱼商品ID" />
        </a-form-item>
        <a-form-item label="价格">
          <a-input-number v-model:value="form.price" :min="0" :precision="2" style="width: 100%" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" placeholder="商品描述" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/api/request'

// 商品 API（独立于其他模块）
const getProducts = (params: any) => request.get('/products', { params })
const createProduct = (data: any) => request.post('/products', data)
const updateProduct = (id: number, data: any) => request.put(`/products/${id}`, data)
const deleteProduct = (id: number) => request.delete(`/products/${id}`)

const searchText = ref('')
const loading = ref(false)
const dataSource = ref<any[]>([])
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const modalVisible = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const form = reactive({ title: '', itemId: '', price: undefined as number | undefined, description: '' })

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '商品名称', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '闲鱼商品ID', dataIndex: 'itemId', key: 'itemId', width: 140 },
  { title: '价格', dataIndex: 'price', key: 'price', width: 80 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '操作', key: 'action', width: 160 },
]

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getProducts({ page: pagination.current, size: pagination.pageSize, keyword: searchText.value })
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
  form.title = record?.title ?? ''
  form.itemId = record?.itemId ?? ''
  form.price = record?.price ?? undefined
  form.description = record?.description ?? ''
  modalVisible.value = true
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    if (editingId.value) {
      await updateProduct(editingId.value, form)
      message.success('更新成功')
    } else {
      await createProduct(form)
      message.success('创建成功')
    }
    modalVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteProduct(id)
  message.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
