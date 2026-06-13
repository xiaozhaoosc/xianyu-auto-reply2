<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between">
      <a-input-search v-model:value="searchText" placeholder="搜索发货规则" @search="loadData" style="width: 250px" />
      <a-button type="primary" @click="openModal()">新增规则</a-button>
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

    <a-modal v-model:open="modalVisible" :title="editingId ? '编辑发货规则' : '新增发货规则'" @ok="handleSubmit" :confirm-loading="submitting" width="600px">
      <a-form :model="form" layout="vertical">
        <a-form-item label="规则名称" :rules="[{ required: true, message: '请输入规则名称' }]">
          <a-input v-model:value="form.name" placeholder="请输入规则名称" />
        </a-form-item>
        <a-form-item label="商品ID">
          <a-input v-model:value="form.itemId" placeholder="闲鱼商品ID" />
        </a-form-item>
        <a-form-item label="卡券模板ID">
          <a-input-number v-model:value="form.cardTemplateId" placeholder="关联卡券模板" style="width: 100%" />
        </a-form-item>
        <a-form-item label="发货内容模板">
          <a-textarea v-model:value="form.deliveryTemplate" placeholder="发货时发送的内容模板，支持 {card_code} 变量" :rows="4" />
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
import { getDeliveryBlockRules, createDeliveryBlockRule, updateDeliveryBlockRule, deleteDeliveryBlockRule } from '@/api/rule'

const searchText = ref('')
const loading = ref(false)
const dataSource = ref<any[]>([])
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const modalVisible = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const form = reactive({ name: '', itemId: '', cardTemplateId: undefined as number | undefined, deliveryTemplate: '', priority: 0 })

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '规则名称', dataIndex: 'name', key: 'name' },
  { title: '商品ID', dataIndex: 'itemId', key: 'itemId', width: 140 },
  { title: '卡券模板ID', dataIndex: 'cardTemplateId', key: 'cardTemplateId', width: 110 },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80 },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '操作', key: 'action', width: 160 },
]

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getDeliveryBlockRules({ page: pagination.current, size: pagination.pageSize, keyword: searchText.value })
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
  form.itemId = record?.itemId ?? ''
  form.cardTemplateId = record?.cardTemplateId ?? undefined
  form.deliveryTemplate = record?.deliveryTemplate ?? ''
  form.priority = record?.priority ?? 0
  modalVisible.value = true
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    if (editingId.value) {
      await updateDeliveryBlockRule(editingId.value, form)
      message.success('更新成功')
    } else {
      await createDeliveryBlockRule(form)
      message.success('创建成功')
    }
    modalVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteDeliveryBlockRule(id)
  message.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
