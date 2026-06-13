<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between">
      <a-input-search v-model:value="searchText" placeholder="搜索素材名称" @search="loadData" style="width: 250px" />
      <a-button type="primary" @click="openModal()">上传素材</a-button>
    </div>

    <a-table :columns="columns" :data-source="dataSource" :loading="loading" :pagination="pagination" @change="handleTableChange" row-key="id">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'type'">
          <a-tag>{{ record.type || '未知' }}</a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button size="small" @click="handlePreview(record)">预览</a-button>
            <a-popconfirm title="确定删除？" @confirm="handleDelete(record.id)">
              <a-button size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 上传弹窗 -->
    <a-modal v-model:open="modalVisible" title="上传素材" @ok="handleSubmit" :confirm-loading="submitting">
      <a-form :model="form" layout="vertical">
        <a-form-item label="素材名称" :rules="[{ required: true, message: '请输入名称' }]">
          <a-input v-model:value="form.name" placeholder="素材名称" />
        </a-form-item>
        <a-form-item label="素材类型">
          <a-select v-model:value="form.type">
            <a-select-option value="IMAGE">图片</a-select-option>
            <a-select-option value="VIDEO">视频</a-select-option>
            <a-select-option value="TEXT">文本</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="素材URL">
          <a-input v-model:value="form.url" placeholder="素材文件URL" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 预览弹窗 -->
    <a-modal v-model:open="previewVisible" title="素材预览" :footer="null" width="600px">
      <div style="text-align: center">
        <img v-if="previewRecord?.type === 'IMAGE'" :src="previewRecord?.url" style="max-width: 100%" />
        <video v-else-if="previewRecord?.type === 'VIDEO'" :src="previewRecord?.url" controls style="max-width: 100%" />
        <p v-else>{{ previewRecord?.url || '暂无预览' }}</p>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const getMaterials = (params: any) => request.get('/materials', { params })
const createMaterial = (data: any) => request.post('/materials', data)
const deleteMaterial = (id: number) => request.delete(`/materials/${id}`)

const searchText = ref('')
const loading = ref(false)
const dataSource = ref<any[]>([])
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const modalVisible = ref(false)
const submitting = ref(false)
const form = reactive({ name: '', type: 'IMAGE', url: '' })

const previewVisible = ref(false)
const previewRecord = ref<any>(null)

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'type', key: 'type', width: 80 },
  { title: 'URL', dataIndex: 'url', key: 'url', ellipsis: true },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '操作', key: 'action', width: 140 },
]

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getMaterials({ page: pagination.current, size: pagination.pageSize, keyword: searchText.value })
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

const openModal = () => {
  form.name = ''
  form.type = 'IMAGE'
  form.url = ''
  modalVisible.value = true
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    await createMaterial(form)
    message.success('上传成功')
    modalVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteMaterial(id)
  message.success('删除成功')
  loadData()
}

const handlePreview = (record: any) => {
  previewRecord.value = record
  previewVisible.value = true
}

onMounted(loadData)
</script>
