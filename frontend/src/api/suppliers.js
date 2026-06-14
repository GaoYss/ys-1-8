import { http } from './http'

export const suppliersApi = {
  list() {
    return http.get('/suppliers')
  },
  create(payload) {
    return http.post('/suppliers', payload)
  },
  update(id, payload) {
    return http.put(`/suppliers/${id}`, payload)
  }
}
