<template>
  <div class="home">
    <div class="hero">
      <h1 class="hero-title">品牌排行榜</h1>
      <p class="hero-sub">来自 chinapp.com 的实时品牌数据，每周自动更新</p>

      <!-- Tab 切换 -->
      <div class="tabs">
        <button
          class="tab-btn"
          :class="{ active: tab === 'browse' }"
          @click="tab = 'browse'"
        >🗂️ 浏览分类</button>
        <button
          class="tab-btn"
          :class="{ active: tab === 'search' }"
          @click="tab = 'search'"
        >🔍 品牌反查</button>
      </div>

      <!-- 浏览模式：类别搜索框 -->
      <SearchBar v-if="tab === 'browse'" @search="store.setSearch" />

      <div class="stats" v-if="stats">
        <span class="stat-item"><span class="stat-num">{{ stats.total_groups }}</span> 大类</span>
        <span class="stat-sep">·</span>
        <span class="stat-item"><span class="stat-num">{{ stats.total_parents }}</span> 中类</span>
        <span class="stat-sep">·</span>
        <span class="stat-item"><span class="stat-num">{{ stats.total_categories }}</span> 小类</span>
        <span class="stat-sep">·</span>
        <span class="stat-item"><span class="stat-num">{{ stats.total_brands }}</span> 个品牌已收录</span>
      </div>
    </div>

    <!-- 内容区 -->
    <GroupList v-if="tab === 'browse'" :auto-open-cat-id="pendingCatId" :auto-open-cat-name="pendingCatName" />
    <BrandSearch v-else @goto-category="gotoCategory" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import SearchBar from '../components/SearchBar.vue'
import GroupList from '../components/GroupList.vue'
import BrandSearch from '../components/BrandSearch.vue'
import { useCategoryStore } from '../stores/category'
import { api } from '../api'

const store = useCategoryStore()
const stats = ref(null)
const tab = ref('browse')
const route = useRoute()

// 从管理后台跳转过来时，自动定位并打开品牌抽屉
const pendingCatId = ref(null)
const pendingCatName = ref(null)

function gotoCategory(cat) {
  store.saveNav(cat.group_name, cat.parent_name || '__none__')
  tab.value = 'browse'
}

onMounted(async () => {
  // 检查是否从管理后台带了 catId 参数
  if (route.query.catId) {
    pendingCatId.value = Number(route.query.catId)
    pendingCatName.value = route.query.catName || ''
  }
  store.fetchGroups()
  try { stats.value = await api.getCrawlerStatus() } catch {}
})
</script>

<style scoped>
.home { padding-bottom: 48px; }

.hero {
  background: #fff;
  border-radius: 12px;
  padding: 24px 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.hero-title { font-size: 24px; font-weight: 800; color: #1a1a2e; margin-bottom: 6px; }
.hero-sub { font-size: 13px; color: #909399; margin-bottom: 16px; }

/* Tab */
.tabs { display: flex; gap: 8px; margin-bottom: 16px; }
.tab-btn {
  padding: 7px 18px;
  border-radius: 20px;
  border: 2px solid #e8eaf6;
  background: #fff;
  color: #606266;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.tab-btn:hover { border-color: #5c6bc0; color: #5c6bc0; }
.tab-btn.active { border-color: #1a1a2e; background: #1a1a2e; color: #fff; }

.stats {
  margin-top: 12px;
  font-size: 13px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.stat-item { display: flex; align-items: baseline; gap: 3px; }
.stat-num { font-size: 16px; font-weight: 700; color: #5c6bc0; }
.stat-sep { color: #dcdfe6; }

@media (max-width: 640px) {
  .hero { padding: 16px; border-radius: 10px; margin-bottom: 12px; }
  .hero-title { font-size: 20px; }
  .hero-sub { display: none; }
}
</style>
