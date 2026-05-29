<template>
  <div class="brand-search">
    <!-- 搜索框 -->
    <div class="search-wrap">
      <el-input
        v-model="keyword"
        placeholder="输入品牌名，如：华为、星巴克、耐克…"
        clearable
        size="large"
        @keyup.enter="doSearch"
        @clear="clear"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
        <template #append>
          <el-button type="primary" @click="doSearch" :loading="loading">查询</el-button>
        </template>
      </el-input>
    </div>

    <!-- 结果 -->
    <template v-if="searched">
      <div v-if="loading" class="hint">查询中…</div>

      <div v-else-if="!results.length" class="empty">
        <el-empty description="暂无数据，该品牌可能尚未被收录" :image-size="80" />
      </div>

      <template v-else>
        <div class="result-header">
          「<strong>{{ lastKeyword }}</strong>」在
          <strong>{{ results.length }}</strong> 个类别的 Top10 中出现
        </div>

        <div class="result-list">
          <div
            v-for="item in results"
            :key="`${item.brand_id}-${item.category.id}`"
            class="result-card"
            @click="emit('goto-category', item.category)"
          >
            <!-- 左：logo + 品牌名 -->
            <div class="brand-col">
              <el-avatar
                v-if="item.logo_url"
                :src="proxyLogo(item.logo_url)"
                :size="40"
                shape="square"
                @error="() => true"
              />
              <el-avatar v-else :size="40" shape="square">{{ item.brand_name[0] }}</el-avatar>
              <div class="brand-info">
                <a
                  v-if="item.detail_url"
                  :href="item.detail_url"
                  target="_blank"
                  class="brand-name"
                >{{ item.brand_name }}</a>
                <span v-else class="brand-name">{{ item.brand_name }}</span>
                <span v-if="item.company_name" class="company-name">{{ item.company_name }}</span>
              </div>
            </div>

            <!-- 右：排名 + 类别路径 -->
            <div class="rank-col">
              <span :class="['rank-badge', `rank-${item.rank}`]">{{ item.rank }}</span>
              <div class="cat-path">
                <span v-if="item.category.group_name" class="path-group">
                  {{ item.category.group_name }}
                </span>
                <span v-if="item.category.parent_name" class="path-sep">›</span>
                <span v-if="item.category.parent_name" class="path-parent">
                  {{ item.category.parent_name }}
                </span>
                <span class="path-sep">›</span>
                <span class="path-cat">{{ item.category.name }}</span>
              </div>
              <div v-if="item.prev_rank && item.prev_rank !== item.rank" class="rank-change">
                <el-tag :type="item.rank < item.prev_rank ? 'success' : 'danger'" size="small">
                  {{ item.rank < item.prev_rank ? '↑' : '↓' }}{{ Math.abs(item.prev_rank - item.rank) }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>

    <!-- 未搜索时的提示 -->
    <div v-else class="hint-idle">
      <p>可查询某个品牌出现在哪些行业的 Top10 排行榜中</p>
      <div class="suggestions">
        <span
          v-for="s in suggestions"
          :key="s"
          class="suggest-tag"
          @click="quickSearch(s)"
        >{{ s }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { api } from '../api'

const props = defineProps({})
const emit = defineEmits(['goto-category'])

const keyword = ref('')
const loading = ref(false)
const searched = ref(false)
const results = ref([])
const lastKeyword = ref('')

const suggestions = ['华为', '小米', '耐克Nike', '星巴克', '肯德基', '海尔', '美的', '格力', '蒙牛', '伊利']

async function doSearch() {
  const q = keyword.value.trim()
  if (!q) return
  loading.value = true
  searched.value = true
  lastKeyword.value = q
  try {
    const res = await api.searchBrands(q)
    results.value = res.items
  } catch {
    results.value = []
  } finally {
    loading.value = false
  }
}

function quickSearch(name) {
  keyword.value = name
  doSearch()
}

function clear() {
  searched.value = false
  results.value = []
}

function proxyLogo(url) {
  if (!url) return ''
  return url.replace(/^https?:\/\/img\.chinapp\.com/, '/img-proxy')
}
</script>

<style scoped>
.brand-search { padding-top: 4px; }

.search-wrap { max-width: 600px; }

.hint { color: #909399; font-size: 14px; padding: 24px 0; text-align: center; }

.empty { padding: 32px 0; }

.result-header {
  font-size: 14px;
  color: #606266;
  margin: 16px 0 10px;
}

.result-list { display: flex; flex-direction: column; gap: 8px; }

.result-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: #fff;
  border-radius: 10px;
  padding: 12px 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: all 0.15s;
  border: 2px solid transparent;
}
.result-card:hover { border-color: #5c6bc0; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(92,107,192,0.12); }

.brand-col { display: flex; align-items: center; gap: 12px; min-width: 0; flex: 1; }
.brand-info { display: flex; flex-direction: column; min-width: 0; }
.brand-name {
  font-size: 14px; font-weight: 600; color: #303133;
  text-decoration: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.brand-name:hover { color: #409eff; }
.company-name { font-size: 11px; color: #909399; margin-top: 2px; }

.rank-col { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex-shrink: 0; }

.rank-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: 50%;
  font-weight: 700; font-size: 13px;
  background: #e8eaf6; color: #5c6bc0;
}
.rank-badge.rank-1 { background: #ffd700; color: #7a5c00; }
.rank-badge.rank-2 { background: #c0c0c0; color: #555; }
.rank-badge.rank-3 { background: #cd7f32; color: #fff; }

.cat-path {
  display: flex; align-items: center; gap: 3px;
  font-size: 12px; flex-wrap: wrap; justify-content: flex-end;
}
.path-group { color: #5c6bc0; font-weight: 500; }
.path-parent { color: #7986cb; }
.path-cat { color: #303133; font-weight: 600; }
.path-sep { color: #c0c4cc; font-size: 11px; }

.rank-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.hint-idle p { font-size: 13px; color: #909399; margin-bottom: 12px; }

.suggestions { display: flex; flex-wrap: wrap; gap: 8px; }
.suggest-tag {
  padding: 4px 12px; border-radius: 16px;
  background: #f0f1fa; color: #5c6bc0;
  font-size: 13px; cursor: pointer;
  transition: all 0.15s;
}
.suggest-tag:hover { background: #5c6bc0; color: #fff; }

@media (max-width: 640px) {
  .result-card { padding: 10px 12px; gap: 10px; }
  .brand-name { font-size: 13px; }
  .cat-path { font-size: 11px; }
}
</style>
