<template>
  <div class="tagged-view">
    <router-link to="/" class="back-link">← 返回首页</router-link>
    <div class="view-header">
      <div class="header-icon">🇨🇳</div>
      <div>
        <h2 class="view-title">国货之光</h2>
        <p class="view-sub">收录各品类中表现优秀的国产品牌，支持国货从这里开始</p>
      </div>
    </div>

    <!-- 大类筛选 -->
    <div class="filter-bar">
      <span
        class="filter-tag"
        :class="{ active: !selectedGroup }"
        @click="selectGroup(null)"
      >全部</span>
      <span
        v-for="g in groups"
        :key="g"
        class="filter-tag"
        :class="{ active: selectedGroup === g }"
        @click="selectGroup(g)"
      >{{ g }}</span>
    </div>

    <!-- 内容 -->
    <div v-if="loading" class="loading-wrap">
      <el-skeleton :rows="5" animated />
    </div>

    <template v-else-if="items.length">
      <div class="brand-list">
        <div v-for="item in items" :key="item.brand_id" class="brand-card">
          <!-- logo -->
          <el-avatar
            v-if="item.logo_url"
            :src="proxyLogo(item.logo_url)"
            :size="44"
            shape="square"
            @error="() => true"
          />
          <el-avatar v-else :size="44" shape="square" style="background:#e6a23c;font-size:18px">🏮</el-avatar>

          <!-- 品牌信息 -->
          <div class="card-info">
            <div class="card-name-row">
              <span class="card-name">{{ item.name }}</span>
              <span class="card-rank">No.{{ item.rank }}</span>
            </div>
            <div class="cat-path">
              <span v-if="item.category.group_name" class="path-group">{{ item.category.group_name }}</span>
              <span v-if="item.category.parent_name" class="path-sep">›</span>
              <span v-if="item.category.parent_name" class="path-parent">{{ item.category.parent_name }}</span>
              <span class="path-sep">›</span>
              <span class="path-cat">{{ item.category.name }}</span>
            </div>
            <div v-if="item.tags && item.tags.length" class="card-tags">
              <el-tag
                v-for="tag in item.tags"
                :key="tag"
                :type="tagType(tag)"
                size="small"
                effect="plain"
                class="card-tag"
              >{{ tag }}</el-tag>
            </div>
            <div v-if="item.brand_note" class="card-note">{{ item.brand_note }}</div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <el-pagination
        v-if="total > pageSize"
        class="pagination"
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="changePage"
      />
    </template>

    <el-empty
      v-else
      description="暂无国货标注数据，可在管理后台为品牌添加「国货之光」标签"
      :image-size="100"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const loading = ref(false)
const items    = ref([])
const total    = ref(0)
const page     = ref(1)
const pageSize = 20
const selectedGroup = ref(null)
const groups = ref([])

async function load() {
  loading.value = true
  try {
    const res = await api.getBrandDomestic({
      group_name: selectedGroup.value || undefined,
      page: page.value,
      page_size: pageSize,
    })
    items.value = res.items || []
    total.value = res.total || 0
    // 后端每次都返回全量大类列表，直接使用
    if (res.groups && res.groups.length) {
      groups.value = res.groups
    }
  } catch {
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function selectGroup(g) {
  selectedGroup.value = g
  page.value = 1
  load()
}

function changePage(p) {
  page.value = p
  load()
}

function proxyLogo(url) {
  if (!url) return ''
  return url.replace(/^https?:\/\/img\.chinapp\.com/, '/img-proxy')
}

function tagType(tag) {
  if (['推荐','国货之光','高性价比','口碑稳定','品质优秀'].includes(tag)) return 'success'
  if (['避雷','❌避雷','有召回记录'].includes(tag)) return 'danger'
  if (['有争议'].includes(tag)) return 'warning'
  return 'info'
}

onMounted(load)
</script>

<style scoped>
.tagged-view { padding-bottom: 48px; }

.back-link {
  display: inline-flex;
  align-items: center;
  font-size: 13px;
  color: #909399;
  text-decoration: none;
  margin-bottom: 12px;
  padding: 4px 2px;
  transition: color 0.15s;
}
.back-link:hover { color: #e6a23c; }

.view-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.header-icon { font-size: 36px; line-height: 1; flex-shrink: 0; }
.view-title { font-size: 22px; font-weight: 800; color: #1a1a2e; margin-bottom: 4px; }
.view-sub { font-size: 13px; color: #909399; }

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}
.filter-tag {
  padding: 5px 14px;
  border-radius: 16px;
  background: #f5f5f5;
  color: #606266;
  font-size: 13px;
  cursor: pointer;
  border: 1.5px solid transparent;
  transition: all 0.15s;
}
.filter-tag:hover { border-color: #e6a23c; color: #e6a23c; }
.filter-tag.active { background: #fdf6ec; border-color: #e6a23c; color: #d48806; font-weight: 600; }

.loading-wrap { padding: 12px 0; }

.brand-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }

.brand-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  background: #fff;
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border-left: 3px solid #e6a23c;
}

.card-info { flex: 1; min-width: 0; }
.card-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.card-name { font-size: 15px; font-weight: 700; color: #303133; }
.card-rank {
  font-size: 12px; color: #909399;
  background: #f5f5f5; border-radius: 8px;
  padding: 1px 7px;
}

.cat-path {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; flex-wrap: wrap; margin-bottom: 6px;
}
.path-group { color: #5c6bc0; font-weight: 500; }
.path-parent { color: #7986cb; }
.path-cat { color: #303133; font-weight: 600; }
.path-sep { color: #c0c4cc; font-size: 11px; }

.card-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 4px; }
.card-tag { font-size: 10px !important; padding: 0 5px !important; height: 17px !important; line-height: 17px !important; }

.card-note {
  font-size: 12px; color: #606266; line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}

.pagination { justify-content: center; }

@media (max-width: 640px) {
  .view-header { padding: 14px; }
  .view-title { font-size: 18px; }
  .brand-card { padding: 10px 12px; gap: 10px; }
}
</style>
