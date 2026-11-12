/**
 * 线索池 API
 *
 * 功能：
 * 1. 线索采集任务的查询与 CRUD、手动扫描
 * 2. 线索商品池 / 线索评论流查询、人工动作记录、建议话术
 * 3. 扫描日志与总览统计
 * 4. Phase 0 探针（单商品评论读取，仅人工验证用）
 *
 * 说明：本模块只读监控别人商品评论区的高意向需求，
 * 不提供任何自动发送评论/私信的接口。
 */
import { del, get, post, put } from '@/utils/request'
import type { ApiResponse } from '@/types'

const PREFIX = '/api/v1/lead-capture'

// ---------------------------------------------------------------------------
// 类型定义
// ---------------------------------------------------------------------------

export type LeadSourceType = 'monitor' | 'keyword'
export type LeadIntentLevel = 'strong' | 'medium' | 'weak'
export type LeadCommentStatus = 'new' | 'reviewed' | 'ignored' | 'followed'
export type LeadItemStatus = 'active' | 'archived'

export interface LeadCaptureTask {
  id: number
  owner_id?: number | null
  name: string
  source_type: LeadSourceType
  keyword?: string | null
  monitor_task_id?: number | null
  price_min?: number | null
  price_max?: number | null
  interval_minutes: number
  max_items_per_round: number
  comment_pages_per_item: number
  include_weak: boolean
  account_ids: string[]
  rescan_cooldown_hours: number
  is_enabled: boolean
  last_run_at?: string | null
  remark?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface LeadItem {
  id: number
  owner_id?: number | null
  item_id: string
  title?: string | null
  price?: string | null
  seller_nick?: string | null
  seller_user_id?: string | null
  item_url?: string | null
  pic_url?: string | null
  want_count?: string | null
  comment_count: number
  strong_count: number
  medium_count: number
  demand_score: number
  first_seen_at?: string | null
  last_seen_at?: string | null
  last_comment_scan_at?: string | null
  status: LeadItemStatus
  created_at?: string | null
}

export interface LeadCommentItemSummary {
  item_id: string
  title?: string | null
  price?: string | null
  item_url?: string | null
  pic_url?: string | null
  seller_nick?: string | null
  demand_score: number
}

export interface LeadComment {
  id: number
  owner_id?: number | null
  lead_item_id: number
  comment_id?: string | null
  commenter_name?: string | null
  commenter_user_id?: string | null
  content: string
  comment_time?: string | null
  intent_level: LeadIntentLevel
  intent_keywords: string[]
  status: LeadCommentStatus
  created_at?: string | null
  item?: LeadCommentItemSummary
}

export interface LeadScanLog {
  id: number
  task_id: number
  task_name?: string | null
  trigger_type: string
  account_id?: string | null
  scanned_count: number
  comment_fetched: number
  comment_new: number
  strong_new: number
  risk_triggered: boolean
  status: string
  message?: string | null
  created_at?: string | null
}

export interface LeadOverview {
  total_tasks: number
  enabled_tasks: number
  total_items: number
  active_items: number
  total_comments: number
  pending_comments: number
  strong_comments: number
  followed_comments: number
  today_new_comments: number
  today_new_strong: number
  trend: Array<{ date: string; strong: number; medium: number; weak: number }>
}

export interface LeadProbeResult {
  success: boolean
  error?: string
  risk_triggered: boolean
  punish_url?: string
  item_invalid: boolean
  account_invalid: boolean
  comment_count: number
  total: number
  sample_comments: Array<{ commenter_name?: string | null; content: string; comment_time?: string | null }>
  raw_keys: string[]
}

export interface LeadPagedData<T> {
  list: T[]
  total: number
  page: number
  page_size: number
}

// ---------------------------------------------------------------------------
// 标签映射
// ---------------------------------------------------------------------------

export const INTENT_LEVEL_LABELS: Record<string, string> = {
  strong: '强意向',
  medium: '中意向',
  weak: '弱意向',
}

export const INTENT_LEVEL_BADGE: Record<string, string> = {
  strong: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  medium: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  weak: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
}

export const COMMENT_STATUS_LABELS: Record<string, string> = {
  new: '未处理',
  reviewed: '已看过',
  ignored: '已忽略',
  followed: '已跟进',
}

export const COMMENT_STATUS_BADGE: Record<string, string> = {
  new: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  reviewed: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  ignored: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500',
  followed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
}

export const SCAN_STATUS_LABELS: Record<string, string> = {
  success: '成功',
  partial: '部分成功',
  failed: '失败',
  risk_stopped: '触发风控终止',
}

export const SCAN_STATUS_BADGE: Record<string, string> = {
  success: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  partial: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  risk_stopped: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
}

// ---------------------------------------------------------------------------
// 任务配置
// ---------------------------------------------------------------------------

export interface LeadTaskPayload {
  name: string
  source_type: LeadSourceType
  keyword?: string | null
  monitor_task_id?: number | null
  price_min?: number | null
  price_max?: number | null
  interval_minutes: number
  max_items_per_round: number
  include_weak: boolean
  account_ids: string[]
  rescan_cooldown_hours: number
  is_enabled: boolean
  remark?: string | null
}

export const getLeadTasks = async (
  page: number,
  pageSize: number,
  params?: { keyword?: string; isEnabled?: boolean },
): Promise<ApiResponse<LeadPagedData<LeadCaptureTask>>> => {
  const query = new URLSearchParams()
  query.set('page', String(page))
  query.set('page_size', String(pageSize))
  if (params?.keyword) query.set('keyword', params.keyword)
  if (params?.isEnabled !== undefined && params.isEnabled !== null) query.set('is_enabled', String(params.isEnabled))
  return get<ApiResponse<LeadPagedData<LeadCaptureTask>>>(`${PREFIX}/tasks?${query.toString()}`)
}

export const createLeadTask = async (payload: LeadTaskPayload): Promise<ApiResponse<{ task: LeadCaptureTask }>> => {
  return post<ApiResponse<{ task: LeadCaptureTask }>>(`${PREFIX}/tasks`, payload)
}

export const updateLeadTask = async (
  taskId: number,
  payload: Partial<LeadTaskPayload>,
): Promise<ApiResponse<{ task: LeadCaptureTask }>> => {
  return put<ApiResponse<{ task: LeadCaptureTask }>>(`${PREFIX}/tasks/${taskId}`, payload)
}

export const updateLeadTaskStatus = async (taskId: number, isEnabled: boolean): Promise<ApiResponse> => {
  return post<ApiResponse>(`${PREFIX}/tasks/${taskId}/status`, { is_enabled: isEnabled })
}

export const deleteLeadTask = async (taskId: number): Promise<ApiResponse> => {
  return del<ApiResponse>(`${PREFIX}/tasks/${taskId}`)
}

export const runLeadTask = async (taskId: number): Promise<ApiResponse> => {
  return post<ApiResponse>(`${PREFIX}/tasks/${taskId}/run`)
}

// ---------------------------------------------------------------------------
// 线索数据（只读展示）
// ---------------------------------------------------------------------------

export const getLeadItems = async (
  page: number,
  pageSize: number,
  params?: { status?: string; keyword?: string; minDemandScore?: number },
): Promise<ApiResponse<LeadPagedData<LeadItem>>> => {
  const query = new URLSearchParams()
  query.set('page', String(page))
  query.set('page_size', String(pageSize))
  if (params?.status) query.set('status', params.status)
  if (params?.keyword) query.set('keyword', params.keyword)
  if (params?.minDemandScore !== undefined) query.set('min_demand_score', String(params.minDemandScore))
  return get<ApiResponse<LeadPagedData<LeadItem>>>(`${PREFIX}/items?${query.toString()}`)
}

export const updateLeadItemStatus = async (
  itemDbId: number,
  status: LeadItemStatus,
): Promise<ApiResponse<{ item: LeadItem }>> => {
  return post<ApiResponse<{ item: LeadItem }>>(`${PREFIX}/items/${itemDbId}/status`, { status })
}

export const getLeadItemComments = async (
  itemDbId: number,
  page: number,
  pageSize: number,
  params?: { intentLevel?: string; status?: string },
): Promise<ApiResponse<LeadPagedData<LeadComment>>> => {
  const query = new URLSearchParams()
  query.set('page', String(page))
  query.set('page_size', String(pageSize))
  if (params?.intentLevel) query.set('intent_level', params.intentLevel)
  if (params?.status) query.set('status', params.status)
  return get<ApiResponse<LeadPagedData<LeadComment>>>(`${PREFIX}/items/${itemDbId}/comments?${query.toString()}`)
}

export const getLeadComments = async (
  page: number,
  pageSize: number,
  params?: { intentLevel?: string; status?: string; keyword?: string },
): Promise<ApiResponse<LeadPagedData<LeadComment>>> => {
  const query = new URLSearchParams()
  query.set('page', String(page))
  query.set('page_size', String(pageSize))
  if (params?.intentLevel) query.set('intent_level', params.intentLevel)
  if (params?.status) query.set('status', params.status)
  if (params?.keyword) query.set('keyword', params.keyword)
  return get<ApiResponse<LeadPagedData<LeadComment>>>(`${PREFIX}/comments?${query.toString()}`)
}

export const recordLeadCommentAction = async (
  commentId: number,
  payload: { action_type: string; suggested_reply?: string | null; note?: string | null },
): Promise<ApiResponse> => {
  return post<ApiResponse>(`${PREFIX}/comments/${commentId}/action`, payload)
}

export const getLeadCommentSuggestions = async (
  commentId: number,
): Promise<ApiResponse<{ comment_id: number; suggestions: string[] }>> => {
  return get<ApiResponse<{ comment_id: number; suggestions: string[] }>>(`${PREFIX}/comments/${commentId}/suggestions`)
}

// ---------------------------------------------------------------------------
// 日志与总览
// ---------------------------------------------------------------------------

export const getLeadLogs = async (
  page: number,
  pageSize: number,
  params?: { taskId?: number; status?: string },
): Promise<ApiResponse<LeadPagedData<LeadScanLog>>> => {
  const query = new URLSearchParams()
  query.set('page', String(page))
  query.set('page_size', String(pageSize))
  if (params?.taskId) query.set('task_id', String(params.taskId))
  if (params?.status) query.set('status', params.status)
  return get<ApiResponse<LeadPagedData<LeadScanLog>>>(`${PREFIX}/logs?${query.toString()}`)
}

export const getLeadOverview = async (): Promise<ApiResponse<LeadOverview>> => {
  return get<ApiResponse<LeadOverview>>(`${PREFIX}/overview`)
}

// ---------------------------------------------------------------------------
// Phase 0 探针（仅人工验证用）
// ---------------------------------------------------------------------------

export const runLeadProbe = async (
  itemId: string,
  accountId: string,
): Promise<ApiResponse<LeadProbeResult>> => {
  return post<ApiResponse<LeadProbeResult>>(`${PREFIX}/probe`, { item_id: itemId, account_id: accountId })
}
