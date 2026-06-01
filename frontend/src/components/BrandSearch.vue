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

    <!-- 全局加载骨架 -->
    <div v-if="loading" class="state-wrap">
      <el-skeleton :rows="4" animated />
    </div>

    <!-- 无结果 -->
    <div v-else-if="searched && !results.length" class="state-wrap">
      <el-empty description="暂无数据，该品牌可能尚未被收录" :image-size="80" />
    </div>

    <!-- 有结果 -->
    <template v-else-if="searched && results.length">
      <!-- 情报摘要 -->
      <div class="summary-bar">
        <div class="summary-left">
          <span class="s-item">
            <span class="s-val">{{ meta.total }}</span>
            <span class="s-lbl">个榜单</span>
          </span>
          <span class="s-div" />
          <span class="s-item" v-if="meta.top_rank">
            <span class="s-val s-accent">No.{{ meta.top_rank }}</span>
            <span class="s-lbl">最高排名</span>
          </span>
          <span class="s-div" v-if="meta.top_rank && meta.group_count" />
          <span class="s-item" v-if="meta.group_count">
            <span class="s-val">{{ meta.group_count }}</span>
            <span class="s-lbl">个大类</span>
          </span>
        </div>
        <div v-if="badges.length" class="badge-row">
          <span v-for="b in badges" :key="b.text" class="badge" :class="b.cls">
            {{ b.icon }} {{ b.text }}
          </span>
        </div>
      </div>

      <!-- 结果列表 -->
      <div class="result-list">
        <div
          v-for="item in results"
          :key="`${item.brand_id}-${item.category.id}`"
          class="result-row"
          :class="{ 'is-open': expandedCatId === item.category.id }"
        >
          <!-- 主行：点击展开/收起 -->
          <div class="row-main" @click="toggleExpand(item)">
            <!-- 排名数字 -->
            <span :class="['rank-num', `rank-${item.rank}`]">{{ item.rank }}</span>

            <!-- Logo -->
            <el-avatar
              v-if="item.logo_url"
              :src="proxyLogo(item.logo_url)"
              :size="36"
              shape="square"
              class="brand-logo"
              @error="() => true"
            />
            <el-avatar
              v-else
              :size="36"
              shape="square"
              class="brand-logo brand-logo--fallback"
            >{{ item.brand_name[0] }}</el-avatar>

            <!-- 文字信息 -->
            <div class="row-info">
              <div class="row-name-line">
                <span class="row-name">{{ item.brand_name }}</span>
                <span
                  v-if="item.prev_rank && item.prev_rank !== item.rank"
                  :class="['rank-delta', item.rank < item.prev_rank ? 'delta-up' : 'delta-dn']"
                >
                  {{ item.rank < item.prev_rank ? '↑' : '↓' }}{{ Math.abs(item.prev_rank - item.rank) }}
                </span>
              </div>
              <div class="row-path">
                <span v-if="item.category.group_name" class="path-seg path-group">{{ item.category.group_name }}</span>
                <span v-if="item.category.parent_name" class="path-arrow">›</span>
                <span v-if="item.category.parent_name" class="path-seg">{{ item.category.parent_name }}</span>
                <span class="path-arrow">›</span>
                <span class="path-seg path-leaf">{{ item.category.name }}</span>
              </div>
              <div v-if="item.tags && item.tags.length" class="row-tags">
                <el-tag
                  v-for="tag in item.tags"
                  :key="tag"
                  :type="brandTagType(tag)"
                  size="small"
                  effect="plain"
                  class="row-tag"
                >{{ tag }}</el-tag>
              </div>
            </div>

            <!-- 展开箭头 -->
            <el-icon :class="['row-chevron', { 'is-open': expandedCatId === item.category.id }]">
              <ArrowDown />
            </el-icon>
          </div>

          <!-- 展开面板：该品类 Top10 -->
          <Transition name="panel">
            <div v-if="expandedCatId === item.category.id" class="top10-panel">
              <div class="panel-header">
                <span class="panel-title">{{ item.category.name }} · Top 10</span>
                <span class="panel-hint">点击条目可前往品类</span>
              </div>

              <!-- 加载中 -->
              <div v-if="catBrandsLoading[item.category.id]" class="panel-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>加载中…</span>
              </div>

              <!-- 品牌列表 -->
              <template v-else-if="catBrandsCache[item.category.id] && catBrandsCache[item.category.id].length">
                <div
                  v-for="b in catBrandsCache[item.category.id]"
                  :key="b.id"
                  class="top10-item"
                  :class="{ 'is-current': isSameBrand(b.name, lastKeyword) }"
                  @click.stop="emit('goto-category', item.category)"
                >
                  <span :class="['t-rank', `rank-${b.rank}`]">{{ b.rank }}</span>
                  <el-avatar
                    v-if="b.logo_url"
                    :src="proxyLogo(b.logo_url)"
                    :size="24"
                    shape="square"
                    class="t-logo"
                    @error="() => true"
                  />
                  <el-avatar v-else :size="24" shape="square" class="t-logo t-logo--fallback">{{ b.name[0] }}</el-avatar>
                  <span class="t-name">{{ b.name }}</span>
                  <span v-if="isSameBrand(b.name, lastKeyword)" class="t-you">本品牌</span>
                  <span
                    v-else-if="b.prev_rank && b.prev_rank !== b.rank"
                    :class="['t-delta', b.rank < b.prev_rank ? 'delta-up' : 'delta-dn']"
                  >{{ b.rank < b.prev_rank ? '↑' : '↓' }}{{ Math.abs(b.prev_rank - b.rank) }}</span>
                </div>
              </template>

              <div v-else class="panel-empty">暂无排名数据</div>
            </div>
          </Transition>
        </div>
      </div>
    </template>

    <!-- 初始引导 -->
    <div v-else class="idle-state">
      <p class="idle-tip">查询品牌出现在哪些行业的 Top10 排行榜中</p>
      <div class="suggestions">
        <span
          v-for="s in suggestions"
          :key="s"
          class="suggest-chip"
          @click="quickSearch(s)"
        >{{ s }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { Search, ArrowDown, Loading } from '@element-plus/icons-vue'
import { api } from '../api'

const emit = defineEmits(['goto-category'])

const keyword    = ref('')
const loading    = ref(false)
const searched   = ref(false)
const results    = ref([])
const lastKeyword = ref('')
const meta = ref({ total: 0, top_rank: null, group_count: 0, groups: [] })

// 每张卡独立的展开 / 缓存 / 加载状态
const expandedCatId   = ref(null)
const catBrandsCache  = reactive({})   // { [catId]: Brand[] }
const catBrandsLoading = reactive({})  // { [catId]: boolean }

const suggestions = ['华为', '小米', '耐克Nike', '星巴克', '肯德基', '海尔', '美的', '格力', '蒙牛', '伊利']

const badges = computed(() => {
  if (!results.value.length) return []
  const list = []
  const { top_rank, total } = meta.value

  if (top_rank === 1)     list.push({ icon: '🥇', text: '行业第一',   cls: 'badge-gold' })
  else if (top_rank <= 3) list.push({ icon: '🏆', text: 'TOP 3',     cls: 'badge-gold' })

  if (total >= 5)         list.push({ icon: '💪', text: '多品类强势', cls: 'badge-blue' })
  else if (total >= 3)    list.push({ icon: '📊', text: '跨3+品类',  cls: 'badge-blue' })

  const allTags = results.value.flatMap(i => i.tags || [])
  if (allTags.includes('国货之光')) list.push({ icon: '🇨🇳', text: '国货之光',   cls: 'badge-red' })
  if (allTags.includes('推荐'))     list.push({ icon: '✅',  text: '编辑推荐',   cls: 'badge-green' })
  if (allTags.includes('避雷'))     list.push({ icon: '⚠️', text: '含避雷记录', cls: 'badge-warn' })

  const rising = results.value.some(i => i.prev_rank && i.rank < i.prev_rank)
  if (rising) list.push({ icon: '📈', text: '上升中', cls: 'badge-green' })

  return list
})

async function toggleExpand(item) {
  const catId = item.category.id

  if (expandedCatId.value === catId) {
    expandedCatId.value = null
    return
  }
  expandedCatId.value = catId

  // 已有缓存，直接显示
  if (catBrandsCache[catId] !== undefined) return

  // 请求数据
  catBrandsLoading[catId] = true
  try {
    const res = await api.getCategoryBrands(catId)
    // API 返回 { category_id, category_name, brands: [...] }
    catBrandsCache[catId] = Array.isArray(res) ? res : (res.brands || res.items || [])
  } catch {
    catBrandsCache[catId] = []
  } finally {
    catBrandsLoading[catId] = false
  }
}

function isSameBrand(brandName, query) {
  if (!query) return false
  return brandName.toLowerCase().startsWith(query.toLowerCase())
}

async function doSearch() {
  const q = keyword.value.trim()
  if (!q) return
  loading.value = true
  searched.value = true
  lastKeyword.value = q
  expandedCatId.value = null
  Object.keys(catBrandsCache).forEach(k => delete catBrandsCache[k])
  Object.keys(catBrandsLoading).forEach(k => delete catBrandsLoading[k])
  try {
    const res = await api.searchBrands(q)
    results.value = res.items || []
    meta.value = {
      total:       res.total ?? results.value.length,
      top_rank:    res.top_rank ?? null,
      group_count: res.group_count ?? 0,
      groups:      res.groups ?? [],
    }
  } catch {
    results.value = []
    meta.value = { total: 0, top_rank: null, group_count: 0, groups: [] }
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
  meta.value = { total: 0, top_rank: null, group_count: 0, groups: [] }
  expandedCatId.value = null
  Object.keys(catBrandsCache).forEach(k => delete catBrandsCache[k])
  Object.keys(catBrandsLoading).forEach(k => delete catBrandsLoading[k])
}

function proxyLogo(url) {
  if (!url) return ''
  return url.replace(/^https?:\/\/img\.chinapp\.com/, '/img-proxy')
}

function brandTagType(tag) {
  if (['推荐','国货之光','高性价比','口碑稳定','创新技术','高端品质','品质优秀'].includes(tag)) return 'success'
  if (['避雷','❌避雷','有召回记录'].includes(tag)) return 'danger'
  if (['有争议'].includes(tag)) return 'warning'
  return 'info'
}
</script>

<style scoped>
.brand-search { padding-top: 4px; }
.search-wrap { max-width: 600px; }
.state-wrap { padding: 24px 0; }

/* ─── 情报摘要条 ──────────────────────────────── */
.summary-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  background: #f4f6ff;
  border: 1px solid #dde2f5;
  border-radius: 10px;
  padding: 10px 16px;
  margin: 12px 0;
}
.summary-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.s-item { display: flex; align-items: baseline; gap: 3px; }
.s-val  { font-size: 17px; font-weight: 700; color: #1a1a2e; }
.s-val.s-accent { color: #5c6bc0; }
.s-lbl  { font-size: 11px; color: #909399; }
.s-div  { width: 1px; height: 14px; background: #c5cae9; flex-shrink: 0; }

.badge-row  { display: flex; flex-wrap: wrap; gap: 5px; }
.badge {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 3px 8px; border-radius: 20px;
  font-size: 11px; font-weight: 500;
}
.badge-gold  { background:#fffbe6; color:#8a6500; border:1px solid #ffe08a; }
.badge-blue  { background:#eef0fb; color:#3f51b5; border:1px solid #c5cae9; }
.badge-green { background:#f0faf0; color:#2e7d32; border:1px solid #a5d6a7; }
.badge-red   { background:#fff0f0; color:#c62828; border:1px solid #ef9a9a; }
.badge-warn  { background:#fff8e1; color:#e65100; border:1px solid #ffcc80; }

/* ─── 结果列表卡片组 ──────────────────────────── */
.result-list {
  border: 1px solid #e4e7f0;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 6px rgba(92,107,192,0.06);
}

.result-row { border-bottom: 1px solid #f0f2f8; }
.result-row:last-child { border-bottom: none; }

/* 主行 */
.row-main {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  cursor: pointer;
  transition: background 0.12s;
  user-select: none;
}
.row-main:hover  { background: #f6f8ff; }
.result-row.is-open > .row-main { background: #eef1ff; }

/* 排名数字 */
.rank-num {
  display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; border-radius: 7px;
  font-weight: 800; font-size: 13px; flex-shrink: 0;
  background: #eef0fa; color: #7986cb;
  letter-spacing: -0.5px;
}
.rank-num.rank-1 { background: #fff3c4; color: #8a6500; }
.rank-num.rank-2 { background: #ececec; color: #555; }
.rank-num.rank-3 { background: #fde8d5; color: #8d4a1a; }

/* logo */
.brand-logo { border-radius: 7px !important; flex-shrink: 0; }
.brand-logo--fallback { background: #e8eaf6 !important; color: #5c6bc0 !important; font-size: 14px !important; }

/* 文字区 */
.row-info { flex: 1; min-width: 0; }

.row-name-line { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }
.row-name {
  font-size: 14px; font-weight: 600; color: #1a1a2e;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.rank-delta { font-size: 11px; font-weight: 600; flex-shrink: 0; }
.delta-up { color: #52c41a; }
.delta-dn { color: #f5222d; }

.row-path { display: flex; align-items: center; gap: 2px; flex-wrap: wrap; }
.path-seg   { font-size: 11px; color: #b0b6c8; }
.path-seg.path-group { color: #7986cb; font-weight: 500; }
.path-seg.path-leaf  { color: #606266; font-weight: 600; }
.path-arrow { font-size: 10px; color: #d0d5ef; }

.row-tags { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 5px; }
.row-tag  { font-size: 10px !important; padding: 0 5px !important; height: 16px !important; line-height: 16px !important; }

/* 展开箭头 */
.row-chevron {
  color: #c0c4cc; font-size: 13px; flex-shrink: 0;
  transition: transform 0.22s cubic-bezier(0.4,0,0.2,1), color 0.15s;
}
.row-chevron.is-open { transform: rotate(180deg); color: #5c6bc0; }

/* ─── Top10 展开面板 ───────────────────────────── */
.top10-panel {
  background: #f7f9ff;
  border-top: 1px solid #e4e7f0;
  padding: 10px 14px 12px;
}

.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px; padding-bottom: 7px;
  border-bottom: 1px solid #e4e7f0;
}
.panel-title { font-size: 12px; font-weight: 700; color: #5c6bc0; letter-spacing: 0.02em; }
.panel-hint  { font-size: 11px; color: #c0c4cc; }

.panel-loading {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: #909399; padding: 10px 0;
}
.panel-empty { font-size: 12px; color: #c0c4cc; padding: 10px 0; text-align: center; }

/* Top10 行 */
.top10-item {
  display: flex; align-items: center; gap: 8px;
  padding: 5px 6px; border-radius: 7px;
  cursor: pointer;
  transition: background 0.1s;
}
.top10-item:hover { background: #eef0fb; }
.top10-item.is-current {
  background: #fffbe6;
  border: 1px solid #ffe58f;
  margin: 2px 0;
}

.t-rank {
  display: inline-flex; align-items: center; justify-content: center;
  width: 20px; height: 20px; border-radius: 5px;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
  background: #eef0fa; color: #7986cb;
}
.t-rank.rank-1 { background: #fff3c4; color: #8a6500; }
.t-rank.rank-2 { background: #ececec; color: #555; }
.t-rank.rank-3 { background: #fde8d5; color: #8d4a1a; }

.t-logo { border-radius: 5px !important; flex-shrink: 0; }
.t-logo--fallback { background: #f0f0f0 !important; color: #bbb !important; font-size: 9px !important; }

.t-name {
  flex: 1; font-size: 13px; color: #303133;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.top10-item.is-current .t-name { font-weight: 700; color: #1a1a2e; }

.t-you   { font-size: 11px; color: #e6a23c; font-weight: 600; flex-shrink: 0; }
.t-delta { font-size: 11px; flex-shrink: 0; }

/* ─── 展开动画 ──────────────────────────────────── */
.panel-enter-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.panel-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.panel-enter-from, .panel-leave-to { opacity: 0; transform: translateY(-6px); }

/* ─── 初始引导 ──────────────────────────────────── */
.idle-state { padding: 4px 0; }
.idle-tip   { font-size: 13px; color: #909399; margin-bottom: 12px; }
.suggestions { display: flex; flex-wrap: wrap; gap: 7px; }
.suggest-chip {
  padding: 5px 14px; border-radius: 20px;
  background: #f0f1fa; color: #5c6bc0;
  font-size: 13px; cursor: pointer;
  border: 1px solid #dde2f5;
  transition: all 0.15s;
}
.suggest-chip:hover { background: #5c6bc0; color: #fff; border-color: #5c6bc0; }

/* ─── 响应式 ────────────────────────────────────── */
@media (max-width: 640px) {
  .row-main { padding: 10px 12px; gap: 8px; }
  .rank-num { width: 22px; height: 22px; font-size: 11px; }
  .row-name { font-size: 13px; }
  .top10-panel { padding: 8px 12px 10px; }
  .summary-bar { padding: 9px 12px; }
}
</style>
