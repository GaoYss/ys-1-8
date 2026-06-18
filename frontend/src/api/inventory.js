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
  get(id) {
    return http.get(`/inventory/${id}`)
  },
  create(payload) {
    return http.post('/inventory', payload)
  },
  update(id, payload) {
    return http.put(`/inventory/${id}`, payload)
  },
  listBatches(params = {}) {
    return http.get('/inventory/batches', { params })
  },
  getBatch(batchId) {
    return http.get(`/inventory/batches/${batchId}`)
  },
  listIngredientBatches(ingredientId, params = {}) {
    return http.get(`/inventory/${ingredientId}/batches`, { params })
  }
}
