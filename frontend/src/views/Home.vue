<template>
  <div class="home">
    <div class="hero">
      <h1 class="hero-title">品牌排行榜</h1>
      <p class="hero-sub">来自 chinapp.com 的实时品牌数据，每周自动更新</p>
      <SearchBar @search="store.setSearch" />
      <div class="stats" v-if="stats">
        <span class="stat-item">
          <span class="stat-num">{{ stats.total_groups }}</span> 大类
        </span>
        <span class="stat-sep">·</span>
        <span class="stat-item">
          <span class="stat-num">{{ stats.total_parents }}</span> 中类
        </span>
        <span class="stat-sep">·</span>
        <span class="stat-item">
          <span class="stat-num">{{ stats.total_categories }}</span> 小类
        </span>
        <span class="stat-sep">·</span>
        <span class="stat-item">
          <span class="stat-num">{{ stats.total_brands }}</span> 个品牌已收录
        </span>
      </div>
    </div>
    <GroupList />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import SearchBar from '../components/SearchBar.vue'
import GroupList from '../components/GroupList.vue'
import { useCategoryStore } from '../stores/category'
import { api } from '../api'

const store = useCategoryStore()
const stats = ref(null)

onMounted(async () => {
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
