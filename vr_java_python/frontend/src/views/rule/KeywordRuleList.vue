<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between">
      <a-input-search v-model:value="searchText" placeholder="搜索关键词" @search="loadData" style="width: 250px" />
      <a-button type="primary" @click="openModal()">新增规则</a-button>
    </div>

    <a-table :columns="columns" :data-source="dataSource" :loading="loading" :pagination="pagination" @change="handleTableChange" row-key="id">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'keywords'">
          <a-tag v-for="kw in (record.keywords || []).slice(0, 3)" :key="kw" style="margin-bottom: 4px">{{ kw }}</a-tag>
          <span v-if="(record.keywords || []).length > 3">...等{{ record.keywords.length }}个</span>
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

    <a-modal v-model:open="modalVisible" :title="editingId ? '编辑关键词规则' : '新增关键词规则'" @ok="handleSubmit" :confirm-loading="submitting" width="600px">
      <a-form :model="form" layout="vertical">
        <a-form-item label="关键词（逗号分隔）" :rules="[{ required: true, message: '请输入关键词' }]">
          <a-input v-model:value="form.keywordsInput" placeholder="例如：价格,多少钱,多少钱啊" />
        </a-form-item>
        <a-form-item label="回复内容" :rules="[{ required: true, message: '请输入回复内容' }]">
          <a-textarea v-model:value="form.replyContent" placeholder="匹配到关键词后的回复内容" :rows="4" />
        </a-form-item>
        <a-form-item label="匹配方式">
          <a-select v-model:value="form.matchType">
            <a-select-option value="CONTAINS">包含匹配</a-select-option>
            <a-select-option value="EXACT">精确匹配</a-select-option>
            <a-select-option value="REGEX">正则匹配</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="优先级">
          <a-input-number v-model:value="form.priority" :min="0" :max="999" style="width: 100%" />
        </a-form-item>
        <a-form-item label="关联账号ID（留空则全部账号生效）">
          <a-input-number v-model:value="form.accountId" placeholder="留空则全部账号" style="width: 100%" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getKeywordRules, createKeywordRule, updateKeywordRule, deleteKeywordRule } from '@/api/rule'

const searchText = ref('')
const loading = ref(false)
const dataSource = ref<any[]>([])
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const modalVisible = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const form = reactive({
  keywordsInput: '',
  replyContent: '',
  matchType: 'CONTAINS',
  priority: 0,
  accountId: undefined as number | undefined,
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '关键词', dataIndex: 'keywords', key: 'keywords', width: 200 },
  { title: '回复内容', dataIndex: 'replyContent', key: 'replyContent', ellipsis: true },
  { title: '匹配方式', dataIndex: 'matchType', key: 'matchType', width: 100 },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80 },
  { title: '操作', key: 'action', width: 160 },
]

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getKeywordRules({ page: pagination.current, size: pagination.pageSize, keyword: searchText.value })
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
  form.keywordsInput = record?.keywords?.join(',') ?? ''
  form.replyContent = record?.replyContent ?? ''
  form.matchType = record?.matchType ?? 'CONTAINS'
  form.priority = record?.priority ?? 0
  form.accountId = record?.accountId ?? undefined
  modalVisible.value = true
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    const payload = { ...form, keywords: form.keywordsInput.split(',').map(s => s.trim()).filter(Boolean) }
    if (editingId.value) {
      await updateKeywordRule(editingId.value, payload)
      message.success('更新成功')
    } else {
      await createKeywordRule(payload)
      message.success('创建成功')
    }
    modalVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteKeywordRule(id)
  message.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
