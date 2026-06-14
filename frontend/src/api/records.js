import { http } from './http'

export const recordsApi = {
  list(params = {}) {
    return http.get('/records', { params })
  },
  create(payload) {
    return http.post('/records', payload)
  }
}
