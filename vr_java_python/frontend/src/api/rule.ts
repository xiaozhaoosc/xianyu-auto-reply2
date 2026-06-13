import request from './request'

// 关键词规则
export const getKeywordRules = (params: any) => request.get('/keyword-rules', { params })
export const createKeywordRule = (data: any) => request.post('/keyword-rules', data)
export const updateKeywordRule = (id: number, data: any) => request.put(`/keyword-rules/${id}`, data)
export const deleteKeywordRule = (id: number) => request.delete(`/keyword-rules/${id}`)

// 发货规则
export const getDeliveryBlockRules = (params: any) => request.get('/delivery-block-rules', { params })
export const createDeliveryBlockRule = (data: any) => request.post('/delivery-block-rules', data)
export const updateDeliveryBlockRule = (id: number, data: any) => request.put(`/delivery-block-rules/${id}`, data)
export const deleteDeliveryBlockRule = (id: number) => request.delete(`/delivery-block-rules/${id}`)

// 默认回复
export const getDefaultReplies = (params: any) => request.get('/default-replies', { params })
export const createDefaultReply = (data: any) => request.post('/default-replies', data)
export const updateDefaultReply = (id: number, data: any) => request.put(`/default-replies/${id}`, data)
export const deleteDefaultReply = (id: number) => request.delete(`/default-replies/${id}`)
