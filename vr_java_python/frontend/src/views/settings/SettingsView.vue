<template>
  <div>
    <a-card title="系统设置" style="margin-bottom: 16px">
      <a-form :model="form" layout="vertical" style="max-width: 600px">
        <a-form-item label="系统名称">
          <a-input v-model:value="form.systemName" placeholder="系统名称" />
        </a-form-item>
        <a-form-item label="自动回复开关">
          <a-switch v-model:checked="form.autoReplyEnabled" />
        </a-form-item>
        <a-form-item label="自动发货开关">
          <a-switch v-model:checked="form.autoDeliveryEnabled" />
        </a-form-item>
        <a-form-item label="Cookie刷新间隔（分钟）">
          <a-input-number v-model:value="form.cookieRefreshInterval" :min="10" :max="1440" style="width: 100%" />
        </a-form-item>
        <a-form-item label="订单同步间隔（分钟）">
          <a-input-number v-model:value="form.orderSyncInterval" :min="1" :max="60" style="width: 100%" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="handleSave" :loading="saving">保存设置</a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <a-card title="通知设置">
      <a-form :model="notifyForm" layout="vertical" style="max-width: 600px">
        <a-form-item label="订单通知开关">
          <a-switch v-model:checked="notifyForm.orderNotifyEnabled" />
        </a-form-item>
        <a-form-item label="Webhook URL">
          <a-input v-model:value="notifyForm.webhookUrl" placeholder="钉钉/企微 Webhook URL" />
        </a-form-item>
        <a-form-item label="Cookie过期通知">
          <a-switch v-model:checked="notifyForm.cookieExpireNotify" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="handleSaveNotify" :loading="savingNotify">保存通知设置</a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const getSettings = () => request.get('/settings')
const updateSettings = (data: any) => request.put('/settings', data)

const saving = ref(false)
const savingNotify = ref(false)

const form = reactive({
  systemName: '闲鱼智能运营平台',
  autoReplyEnabled: true,
  autoDeliveryEnabled: true,
  cookieRefreshInterval: 120,
  orderSyncInterval: 5,
})

const notifyForm = reactive({
  orderNotifyEnabled: true,
  webhookUrl: '',
  cookieExpireNotify: true,
})

const loadSettings = async () => {
  try {
    const res: any = await getSettings()
    if (res.data) {
      Object.assign(form, res.data)
      if (res.data.notify) {
        Object.assign(notifyForm, res.data.notify)
      }
    }
  } catch {
    // 首次加载失败使用默认值
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await updateSettings(form)
    message.success('设置已保存')
  } finally {
    saving.value = false
  }
}

const handleSaveNotify = async () => {
  savingNotify.value = true
  try {
    await updateSettings({ notify: notifyForm })
    message.success('通知设置已保存')
  } finally {
    savingNotify.value = false
  }
}

onMounted(loadSettings)
</script>
