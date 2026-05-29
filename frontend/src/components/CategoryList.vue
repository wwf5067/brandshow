<template>
  <div class="category-list">
    <el-skeleton :loading="store.loading" :rows="6" animated>
      <template #default>
        <el-empty v-if="!store.categories.length" description="没有找到匹配的类别" />

        <el-collapse v-else v-model="activeNames" @change="onCollapseChange">
          <CategoryItem
            v-for="cat in store.categories"
            :key="cat.id"
            :category="cat"
          />
        </el-collapse>

        <div v-if="store.total > store.pageSize" class="pagination">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="store.pageSize"
            :total="store.total"
            layout="prev, pager, next, total"
            background
            @current-change="store.setPage"
          />
        </div>
      </template>
    </el-skeleton>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import CategoryItem from './CategoryItem.vue'
import { useCategoryStore } from '../stores/category'

const store = useCategoryStore()
const activeNames = ref([])
const currentPage = ref(1)

watch(() => store.page, (p) => { currentPage.value = p })

function onCollapseChange(names) {
  // names 是当前所有展开项的 id 数组，确保每个都加载了品牌数据
  const arr = Array.isArray(names) ? names : [names]
  arr.forEach(id => {
    if (id) store.fetchBrands(Number(id))
  })
}
</script>

<style scoped>
.category-list { margin-top: 20px; }

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

:deep(.el-collapse-item__header) {
  padding: 0 16px;
  height: 56px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 4px;
}

:deep(.el-collapse-item__wrap) {
  background: #fafafa;
  border-radius: 0 0 8px 8px;
  margin-bottom: 8px;
}

:deep(.el-collapse-item__content) {
  padding: 8px 16px 16px;
}

:deep(.el-collapse) {
  border: none;
}
</style>
