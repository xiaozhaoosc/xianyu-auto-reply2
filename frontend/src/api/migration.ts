import { get, post, put } from '@/utils/request'

const MIGRATION_PREFIX = '/api/v1/migration'

export interface SourceItem {
  item_id: string
  title?: string
  price?: string
  card_count: number
  card_names: string[]
}

export interface MigrationBatch {
  id: number
  source_account_id: string
  target_account_id: string
  status: 'prepared' | 'running' | 'paused' | 'done' | 'cancelled'
  total: number
  published: number
  failed: number
  min_interval: number
  max_interval: number
  next_run_at?: string | null
  next_run_in_seconds?: number | null
  last_error?: string | null
  created_at?: string | null
  started_at?: string | null
  finished_at?: string | null
}

export interface MigrationTask {
  id: number
  source_item_id: string
  title: string
  price?: string
  category_id?: string
  category_override?: { cat_name?: string; channel_cat_id?: string; channel_cat_name?: string } | null
  description?: string
  image_count: number
  first_image?: string | null
  status: 'pending' | 'publishing' | 'done' | 'failed' | 'skipped'
  new_item_id?: string | null
  error?: string | null
  attempts: number
  published_at?: string | null
}

export interface CategoryCandidate {
  cat_id?: string | null
  cat_name?: string | null
  channel_cat_id?: string | null
  channel_cat_name?: string | null
  tb_cat_id?: string | null
  is_selected: boolean
  may_need_isbn: boolean
}

export interface BatchDetail {
  batch: MigrationBatch & { description_template?: string }
  tasks: MigrationTask[]
  cards_copied: number
}

export interface CreateBatchRequest {
  source_account_id: string
  target_account_id: string
  item_ids?: string[]
  description_template?: string
  min_interval?: number
  max_interval?: number
}

// 预览源账号中有卡券关联的商品
export const getSourceItems = (sourceAccountId: string): Promise<{ success: boolean; data: { total: number; items: SourceItem[] } }> => {
  return get(`${MIGRATION_PREFIX}/source-items?source_account_id=${encodeURIComponent(sourceAccountId)}`)
}

// 创建迁移批次
export const createBatch = (req: CreateBatchRequest): Promise<{ success: boolean; message: string; data: { batch_id: number; total: number; cards_copied: number; missing_material_count: number } }> => {
  return post(`${MIGRATION_PREFIX}/batches`, req)
}

// 批次列表
export const getBatches = (): Promise<{ success: boolean; data: { batches: MigrationBatch[] } }> => {
  return get(`${MIGRATION_PREFIX}/batches`)
}

// 批次详情
export const getBatchDetail = (batchId: number): Promise<{ success: boolean; data: BatchDetail }> => {
  return get(`${MIGRATION_PREFIX}/batches/${batchId}`)
}

// 批次控制
export const startBatch = (batchId: number): Promise<{ success: boolean; message: string }> => {
  return post(`${MIGRATION_PREFIX}/batches/${batchId}/start`)
}

export const pauseBatch = (batchId: number): Promise<{ success: boolean; message: string }> => {
  return post(`${MIGRATION_PREFIX}/batches/${batchId}/pause`)
}

export const cancelBatch = (batchId: number): Promise<{ success: boolean; message: string }> => {
  return post(`${MIGRATION_PREFIX}/batches/${batchId}/cancel`)
}

// 编辑任务（发布前/失败后可改）
export const updateMigrationTask = (
  taskId: number,
  req: {
    title?: string
    price?: string
    description?: string
    category_override?: { cat_name: string; channel_cat_id: string; channel_cat_name?: string }
    clear_category_override?: boolean
  }
): Promise<{ success: boolean; message: string }> => {
  return put(`${MIGRATION_PREFIX}/tasks/${taskId}`, req)
}

// 获取任务可选类目候选（走闲鱼工作台推荐接口，一轮）
export const getCategoryCandidates = (
  taskId: number
): Promise<{ success: boolean; message?: string; data: { candidates: CategoryCandidate[] } }> => {
  return get(`${MIGRATION_PREFIX}/tasks/${taskId}/category-candidates`)
}

// 重置失败/跳过任务重新发布
export const retryTask = (taskId: number): Promise<{ success: boolean; message: string }> => {
  return post(`${MIGRATION_PREFIX}/tasks/${taskId}/retry`)
}
