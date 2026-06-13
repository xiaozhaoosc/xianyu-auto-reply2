import request from './request'

export const getCards = (params: any) => request.get('/cards', { params })
export const getCard = (id: number) => request.get(`/cards/${id}`)
export const createCard = (data: any) => request.post('/cards', data)
export const updateCard = (id: number, data: any) => request.put(`/cards/${id}`, data)
export const deleteCard = (id: number) => request.delete(`/cards/${id}`)
export const bindItem = (id: number, data: any) => request.post(`/cards/${id}/bind-item`, data)
export const unbindItem = (id: number, data: any) => request.delete(`/cards/${id}/unbind-item`, { data })
