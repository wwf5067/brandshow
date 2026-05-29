<template>
  <el-collapse-item :name="category.id">
    <template #title>
      <div class="cat-header">
        <span class="cat-name">{{ category.name }}</span>
        <div class="cat-meta">
          <el-tag v-if="category.parent_name" size="small" type="info" effect="plain">
            {{ category.parent_name }}
          </el-tag>
          <el-tag size="small" effect="plain">{{ category.brand_count }} 品牌</el-tag>
          <span v-if="category.last_crawled_at" class="crawl-time">
            更新于 {{ formatDate(category.last_crawled_at) }}
          </span>
          <span v-else class="crawl-time no-data">未爬取</span>
        </div>
      </div>
    </template>
    <BrandTable :category-id="category.id" />
  </el-collapse-item>
</template>

<script setup>
import BrandTable from './BrandTable.vue'
import { useCategoryStore } from '../stores/category'

const props = defineProps({
  category: { type: Object, required: true },
})

const store = useCategoryStore()

function handleOpen(id) {
  store.fetchBrands(id)
}

// expose so parent can call
defineExpose({ handleOpen })

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.cat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 2px 0;
}

.cat-name {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  min-width: 120px;
}

.cat-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.crawl-time {
  font-size: 12px;
  color: #909399;
}

.crawl-time.no-data {
  color: #f56c6c;
}
</style>
