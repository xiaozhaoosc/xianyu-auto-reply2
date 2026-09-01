import { post } from '@/utils/request'

const PREFIX = '/api/v1/account-sync'

export interface AccountSyncRequest {
  source_account_id: string
  target_account_ids: string[]
  keyword_filter?: string
  min_price?: number
  max_price?: number
  sync_mode?: string
}

export interface AccountSyncResult {
  batch_id: string
  source_items_count: number
  materials_created: number
  target_accounts_count: number
  publish_result?: {
    success_count?: number
    failed_count?: number
    [key: string]: unknown
  }
}

export interface AccountSyncResponse {
  success: boolean
  message: string
  data?: AccountSyncResult
}

/** 多账号商品同步：源账号商品 → 素材库中转 → 批量发布到目标账号 */
export const syncAccounts = async (payload: AccountSyncRequest): Promise<AccountSyncResponse> => {
  return await post<AccountSyncResponse>(`${PREFIX}/sync`, payload, { timeout: 580000 })
}
