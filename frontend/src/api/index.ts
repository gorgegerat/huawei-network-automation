import apiClient from './client'

export const authAPI = {
  login: (username: string, password: string, captcha?: string) =>
    apiClient.post('/api/auth/login', new URLSearchParams({ username, password, ...(captcha ? { captcha } : {}) }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  register: (username: string, email: string, password: string) =>
    apiClient.post('/api/auth/register', null, { params: { username, email, password } }),
  getMe: () => apiClient.get('/api/auth/me'),
  changePassword: (oldPassword: string, newPassword: string, token: string) =>
    apiClient.post('/api/auth/change-password', { old_password: oldPassword, new_password: newPassword }, {
      headers: { Authorization: `Bearer ${token}` }
    }),
  getCaptcha: () => apiClient.get('/api/auth/captcha'),
}

export const devicesAPI = {
  getAll: () => apiClient.get('/api/devices'),
  getById: (id: number) => apiClient.get(`/api/devices/${id}`),
  create: (data: any) => apiClient.post('/api/devices', data),
  update: (id: number, data: any) => apiClient.put(`/api/devices/${id}`, data),
  delete: (id: number) => apiClient.delete(`/api/devices/${id}`),
  connect: (id: number) => apiClient.post(`/api/devices/${id}/connect`),
  disconnect: (id: number) => apiClient.post(`/api/devices/${id}/disconnect`),
  discover: (id: number) => apiClient.post(`/api/devices/${id}/discover`),
  getGroups: () => apiClient.get('/api/devices/groups/list'),
  getByGroup: (groupName: string) => apiClient.get(`/api/devices/group/${groupName}`),
  updateGroup: (id: number, group: string) => apiClient.put(`/api/devices/${id}/group`, null, { params: { group } }),
  import: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/api/devices/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  export: (format: string = 'excel') => apiClient.get(`/api/devices/export?format=${format}`, { responseType: 'blob' }),
}

export const configsAPI = {
  getByDevice: (deviceId: number) => apiClient.get(`/api/configs/device/${deviceId}`),
  getById: (id: number) => apiClient.get(`/api/configs/${id}`),
  create: (data: any) => apiClient.post('/api/configs', data),
  activate: (id: number) => apiClient.post(`/api/configs/${id}/activate`),
  deploy: (id: number) => apiClient.post(`/api/configs/${id}/deploy`),
  delete: (id: number) => apiClient.delete(`/api/configs/${id}`),
}

export const monitoringAPI = {
  getDeviceMetrics: (deviceId: number, params?: any) =>
    apiClient.get(`/api/monitoring/device/${deviceId}`, { params }),
  getLatestMetrics: (deviceId: number) =>
    apiClient.get(`/api/monitoring/device/${deviceId}/latest`),
  getDeviceSummary: (deviceId: number) =>
    apiClient.get(`/api/monitoring/device/${deviceId}/summary`),
  refreshMetrics: (deviceId: number) =>
    apiClient.post(`/api/monitoring/device/${deviceId}/refresh`),
  forceStop: () => apiClient.post('/api/monitoring/force-stop'),
  getStatus: () => apiClient.get('/api/monitoring/status'),
  exportResults: (params?: any) => apiClient.get('/api/monitoring/export', { params, responseType: 'blob' }),
}

export const alertsAPI = {
  getAll: (params?: any) => apiClient.get('/api/alerts', { params }),
  getById: (id: number) => apiClient.get(`/api/alerts/${id}`),
  resolve: (id: number) => apiClient.post(`/api/alerts/${id}/resolve`),
  getStats: () => apiClient.get('/api/alerts/stats/summary'),
}

export const optimizationAPI = {
  getLogs: (params?: any) => apiClient.get('/api/optimization/logs', { params }),
  trigger: (deviceId: number) => apiClient.post(`/api/optimization/trigger/${deviceId}`),
  optimizeRoute: (deviceId: number) => apiClient.post(`/api/optimization/route/optimize/${deviceId}`),
  getStatus: () => apiClient.get('/api/optimization/status'),
}
