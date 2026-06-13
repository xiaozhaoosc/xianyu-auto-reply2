<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between">
      <a-input-search v-model:value="searchText" placeholder="搜索默认回复" @search="loadData" style="width: 250px" />
      <a-button type="primary" @click="openModal()">新增默认回复</a-button>
    </div>

    <a-table :columns="columns" :data-source="dataSource" :loading="loading" :pagination="pagination" @change="handleTableChange" row-key="id">
      <template #bodyCell="{ column, record }">
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

    <a-modal v-model:open="modalVisible" :title="editingId ? '编辑默认回复' : '新增默认回复'" @ok="handleSubmit" :confirm-loading="submitting" width="600px">
      <a-form :model="form" layout="vertical">
        <a-form-item label="回复内容" :rules="[{ required: true, message: '请输入回复内容' }]">
          <a-textarea v-model:value="form.content" placeholder="当没有匹配到关键词规则时的默认回复" :rows="4" />
        </a-form-item>
        <a-form-item label="关联账号ID（留空则全部账号生效）">
          <a-input-number v-model:value="form.accountId" placeholder="留空则全部账号" style="width: 100%" />
        </a-form-item>
        <a-form-item label="优先级">
          <a-input-number v-model:value="form.priority" :min="0" :max="999" style="width: 100%" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getDefaultReplies, createDefaultReply, updateDefaultReply, deleteDefaultReply } from '@/api/rule'

const searchText = ref('')
const loading = ref(false)
const dataSource = ref<any[]>([])
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const modalVisible = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const form = reactive({ content: '', accountId: undefined as number | undefined, priority: 0 })

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '回复内容', dataIndex: 'content', key: 'content', ellipsis: true },
  { title: '关联账号ID', dataIndex: 'accountId', key: 'accountId', width: 110 },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80 },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '操作', key: 'action', width: 160 },
]

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getDefaultReplies({ page: pagination.current, size: pagination.pageSize, keyword: searchText.value })
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
  form.content = record?.content ?? ''
  form.accountId = record?.accountId ?? undefined
  form.priority = record?.priority ?? 0
  modalVisible.value = true
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    if (editingId.value) {
      await updateDefaultReply(editingId.value, form)
      message.success('更新成功')
    } else {
      await createDefaultReply(form)
      message.success('创建成功')
    }
    modalVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteDefaultReply(id)
  message.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
