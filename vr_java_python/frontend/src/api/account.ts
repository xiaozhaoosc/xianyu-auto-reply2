import request from './request'

export const getAccounts = (params: any) => request.get('/accounts', { params })
export const getAccount = (id: number) => request.get(`/accounts/${id}`)
export const createAccount = (data: any) => request.post('/accounts', data)
export const updateAccount = (id: number, data: any) => request.put(`/accounts/${id}`, data)
export const deleteAccount = (id: number) => request.delete(`/accounts/${id}`)
export const loginAccount = (id: number) => request.post(`/accounts/${id}/login`)
export const refreshCookie = (id: number) => request.post(`/accounts/${id}/refresh-cookie`)
export const updateAccountStatus = (id: number, status: string) => request.put(`/accounts/${id}/status`, { status })
