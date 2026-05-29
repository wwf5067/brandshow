import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

export const api = {
  getCategories({ search = '', group_name = '', parent_name = '', page = 1, page_size = 20 } = {}) {
    return http.get('/categories', { params: { search, group_name, parent_name, page, page_size } })
  },
  getCategoriesMeta() {
    return http.get('/categories/meta')
  },
  getCategoryGroups(search = '') {
    return http.get('/categories/groups', { params: { search } })
  },
  getCategory(id) {
    return http.get(`/categories/${id}`)
  },
  getCategoryBrands(id) {
    return http.get(`/categories/${id}/brands`)
  },
  getCrawlerStatus() {
    return http.get('/crawler/status')
  },
  triggerDiscover() {
    return http.post('/crawler/discover')
  },
  triggerCategory(id) {
    return http.post(`/crawler/trigger/${id}`)
  },
  triggerWeeklySchedule() {
    return http.post('/crawler/schedule/weekly')
  },
  triggerDailyRun() {
    return http.post('/crawler/run/daily')
  },
  searchBrands(name) {
    return http.get('/brands/search', { params: { name } })
  },
}
