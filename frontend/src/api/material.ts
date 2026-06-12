import { post, get } from '@/utils/request'
import type { ApiResponse } from '@/types'

// ==================== 采集到素材库 ====================

export interface CollectToMaterialData {
  item_id: string
  title: string
  price: string
  description?: string
  main_image?: string
  item_url?: string
  area?: string
  seller_name?: string
}

/** 将搜索结果采集到素材库 */
export const collectToMaterial = (data: CollectToMaterialData): Promise<ApiResponse<{ material_id: number }>> => {
  return post('/api/v1/items/collect-to-material', data)
}

// ==================== 账号列表 ====================

export interface AccountOption {
  pk: number
  id: string
  enabled: boolean
  remark?: string
}

/** 获取账号下拉选项 */
export const getAccountOptions = (): Promise<AccountOption[]> => {
  return get('/api/v1/cookies/options')
}

// ==================== 发布 ====================

export interface PublishSingleData {
  account_id: string
  title: string
  description: string
  price: number
  images: string[]
  address?: string
  delivery_method?: string
  postage?: number
  brand?: string
  condition?: string
}

/** 单品发布 */
export const publishSingle = (data: PublishSingleData): Promise<ApiResponse> => {
  return post('/api/v1/product-publish/publish/single', data)
}
