import request from './request'

export const getOrders = (params: any) => request.get('/orders', { params })
export const getOrder = (id: number) => request.get(`/orders/${id}`)
export const syncOrders = () => request.post('/orders/sync')
export const manualDelivery = (id: number, data: any) => request.put(`/orders/${id}/delivery`, data)
