import { defineStore } from 'pinia'
import { api } from '../api'

export const useCategoryStore = defineStore('category', {
  state: () => ({
    groups: [],
    ungrouped: [],
    loading: false,
    searchKeyword: '',
    brandsCache: {},
    brandsLoading: {},
    // 导航状态——路由切换后返回时恢复
    navGroup: null,
    navParent: null,
  }),

  actions: {
    async fetchGroups() {
      this.loading = true
      try {
        const res = await api.getCategoryGroups(this.searchKeyword)
        this.groups = res.groups
        this.ungrouped = res.ungrouped
      } finally {
        this.loading = false
      }
    },

    async fetchBrands(categoryId, force = false) {
      if (!force && this.brandsCache[categoryId] !== undefined) return
      this.brandsLoading[categoryId] = true
      try {
        const res = await api.getCategoryBrands(categoryId)
        this.brandsCache[categoryId] = res.brands
      } finally {
        this.brandsLoading[categoryId] = false
      }
    },

    clearBrandsCache(categoryId) {
      delete this.brandsCache[categoryId]
    },

    setSearch(kw) {
      this.searchKeyword = kw
      this.navGroup = null
      this.navParent = null
      this.fetchGroups()
    },

    saveNav(group, parent) {
      this.navGroup = group
      this.navParent = parent
    },
  },
})
