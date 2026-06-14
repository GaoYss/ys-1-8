import { http } from './http'

export const inventoryApi = {
  list(params = {}) {
    return http.get('/inventory', { params })
  },
  summary() {
    return http.get('/inventory/summary')
  },
  options() {
    return http.get('/inventory/options')
  },
  create(payload) {
    return http.post('/inventory', payload)
  },
  update(id, payload) {
    return http.put(`/inventory/${id}`, payload)
  }
}
