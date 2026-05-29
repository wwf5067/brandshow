<template>
  <div class="group-list">
    <el-skeleton :loading="store.loading" :rows="6" animated>
      <template #default>
        <el-empty v-if="!store.groups.length" description="没有找到匹配的类别" />

        <template v-else>
          <!-- ── 面包屑 ── -->
          <div v-if="activeGroup" class="breadcrumb">
            <span class="bc-item bc-link" @click="resetAll">全部分类</span>
            <span class="bc-sep">›</span>
            <span
              class="bc-item"
              :class="activeParent ? 'bc-link' : 'bc-current'"
              @click="activeParent = null; activeCat = null"
            >{{ activeGroup === '__ungrouped__' ? '未归类' : activeGroup }}</span>
            <template v-if="activeParent">
              <span class="bc-sep">›</span>
              <span class="bc-item bc-current">{{ activeParent === '__none__' ? '其他' : activeParent }}</span>
            </template>
          </div>

          <!-- ── 搜索结果：直接平铺小类 ── -->
          <template v-if="store.searchKeyword">
            <div class="cat-grid">
              <div
                v-for="cat in searchCats"
                :key="cat.id"
                class="cat-card"
                :class="{ active: activeCat === cat.id, 'no-data': !cat.brand_count }"
                @click="openBrands(cat)"
              >
                <span class="cat-card-name">{{ cat.name }}</span>
                <el-tag size="small" :type="cat.brand_count ? 'success' : 'info'" effect="plain">
                  {{ cat.brand_count }} 品牌
                </el-tag>
              </div>
            </div>
          </template>

          <!-- ── 正常模式 ── -->
          <template v-else>
            <!-- 第一层：大类卡片 -->
            <div v-if="!activeGroup" class="group-grid">
              <div
                v-for="group in sortedGroups"
                :key="group.group_name"
                class="group-card"
                @click="selectGroup(group.group_name)"
              >
                <span class="group-icon">{{ groupIcon(group.group_name) }}</span>
                <span class="group-card-name">{{ group.group_name }}</span>
                <span class="group-card-count">{{ group.total_categories }}</span>
              </div>
              <div
                v-if="store.ungrouped.length"
                class="group-card ungrouped"
                @click="selectGroup('__ungrouped__')"
              >
                <span class="group-icon">📦</span>
                <span class="group-card-name">未归类</span>
                <span class="group-card-count">{{ store.ungrouped.length }}</span>
              </div>
            </div>

            <!-- 第二层：中类 -->
            <div v-else-if="activeGroup && !activeParent">
              <div v-if="hasParents" class="parent-grid">
                <div
                  v-for="p in activeGroupParents"
                  :key="p.parent_name || '__none__'"
                  class="parent-card"
                  @click="selectParent(p.parent_name || '__none__')"
                >
                  <span class="parent-card-name">{{ p.parent_name || '其他' }}</span>
                  <span class="parent-card-count">{{ p.categories.length }}</span>
                </div>
              </div>
              <!-- 无中类，直接显示小类 -->
              <div v-else class="cat-grid">
                <div
                  v-for="cat in noParentCats"
                  :key="cat.id"
                  class="cat-card"
                  :class="{ active: activeCat === cat.id, 'no-data': !cat.brand_count }"
                  @click="openBrands(cat)"
                >
                  <span class="cat-card-name">{{ cat.name }}</span>
                  <el-tag size="small" :type="cat.brand_count ? 'success' : 'info'" effect="plain">
                    {{ cat.brand_count }} 品牌
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- 第三层：小类 -->
            <div v-else-if="activeParent" class="cat-grid">
              <div
                v-for="cat in activeCats"
                :key="cat.id"
                class="cat-card"
                :class="{ active: activeCat === cat.id, 'no-data': !cat.brand_count }"
                @click="openBrands(cat)"
              >
                <span class="cat-card-name">{{ cat.name }}</span>
                <el-tag size="small" :type="cat.brand_count ? 'success' : 'info'" effect="plain">
                  {{ cat.brand_count }} 品牌
                </el-tag>
              </div>
            </div>
          </template>
        </template>
      </template>
    </el-skeleton>

    <!-- ── 品牌抽屉：桌面侧边，手机底部 ── -->
    <el-drawer
      v-model="drawerVisible"
      :title="drawerTitle"
      :direction="isMobile ? 'btt' : 'rtl'"
      :size="isMobile ? '85%' : '520px'"
      :append-to-body="true"
    >
      <template #header>
        <div class="drawer-header">
          <div class="drawer-title-row">
            <div class="drawer-title">{{ drawerTitle }}</div>
            <el-button
              size="small"
              :loading="crawling"
              :type="drawerCat && !drawerCat.last_crawled_at ? 'primary' : 'default'"
              @click="triggerCrawl"
            >
              <el-icon v-if="!crawling"><Refresh /></el-icon>
              {{ crawling ? '爬取中...' : (drawerCat && !drawerCat.last_crawled_at ? '立即爬取' : '重新爬取') }}
            </el-button>
          </div>
          <div v-if="drawerCat" class="drawer-meta">
            <span v-if="drawerCat.group_name" class="meta-path">
              {{ drawerCat.group_name }}
              <span v-if="drawerCat.parent_name"> › {{ drawerCat.parent_name }}</span>
              › {{ drawerCat.name }}
            </span>
            <el-tag v-if="drawerCat.last_crawled_at" size="small" type="info">
              {{ formatDate(drawerCat.last_crawled_at) }} 更新
            </el-tag>
            <el-tag v-else size="small" type="warning">未爬取</el-tag>
          </div>
        </div>
      </template>
      <BrandTable v-if="drawerCatId" :key="brandTableKey" :category-id="drawerCatId" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import BrandTable from './BrandTable.vue'
import { useCategoryStore } from '../stores/category'
import { api } from '../api'

const store = useCategoryStore()

const activeGroup = ref(store.navGroup)
const activeParent = ref(store.navParent)
const activeCat = ref(null)
const drawerVisible = ref(false)
const drawerCatId = ref(null)
const drawerCat = ref(null)
const drawerTitle = ref('')
const crawling = ref(false)
const brandTableKey = ref(0)  // 用于强制重新挂载 BrandTable

// 响应式：判断是否手机
const isMobile = ref(window.innerWidth <= 640)
function onResize() { isMobile.value = window.innerWidth <= 640 }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))

// 大类图标映射
const GROUP_ICONS = {
  '手机数码': '📱', '家用电器': '🏠', '服饰鞋帽': '👗', '化妆美容': '💄',
  '食品饮料': '🍜', '餐饮行业': '🍽️', '母婴用品': '👶', '家居生活': '🛋️',
  '箱包首饰': '👜', '汽车用品': '🚗', '工程机械': '🏗️', '教育培训': '📚',
  '办公器材': '💼', '医疗保健': '🏥', '电脑用品': '💻', '农业化工': '🌾',
  '休闲娱乐': '🎮', '成人保健': '💊', '装修建材': '🔨', '金融信息': '💰',
  '其他': '📌', '未归类': '📦',
}

// 大类排序（常用在前）
const GROUP_ORDER = [
  '手机数码', '家用电器', '服饰鞋帽', '化妆美容', '食品饮料',
  '餐饮行业', '母婴用品', '家居生活', '箱包首饰', '汽车用品',
  '电脑用品', '教育培训', '医疗保健', '办公器材', '休闲娱乐',
  '工程机械', '装修建材', '农业化工', '成人保健', '金融信息', '其他',
]

const sortedGroups = computed(() => {
  return [...store.groups].sort((a, b) => {
    const ia = GROUP_ORDER.indexOf(a.group_name)
    const ib = GROUP_ORDER.indexOf(b.group_name)
    if (ia === -1 && ib === -1) return a.group_name.localeCompare(b.group_name)
    if (ia === -1) return 1
    if (ib === -1) return -1
    return ia - ib
  })
})

function groupIcon(name) {
  return GROUP_ICONS[name] || '📂'
}

const searchCats = computed(() => {
  const all = []
  for (const g of store.groups) {
    for (const p of g.parents) all.push(...p.categories)
  }
  all.push(...store.ungrouped)
  return all
})

const activeGroupParents = computed(() => {
  if (!activeGroup.value || activeGroup.value === '__ungrouped__') return []
  const g = store.groups.find(g => g.group_name === activeGroup.value)
  return g ? g.parents : []
})

const hasParents = computed(() =>
  activeGroupParents.value.some(p => p.parent_name !== null)
)

// 无中类时直接显示的小类
const noParentCats = computed(() =>
  activeGroupParents.value.flatMap(p => p.categories)
)

const activeCats = computed(() => {
  if (!activeParent.value) return []
  const p = activeGroupParents.value.find(
    p => (p.parent_name || '__none__') === activeParent.value
  )
  return p ? p.categories : []
})

function selectGroup(name) {
  activeGroup.value = name
  activeParent.value = null
  activeCat.value = null
  store.saveNav(name, null)
}

function selectParent(key) {
  activeParent.value = key
  activeCat.value = null
  store.saveNav(activeGroup.value, key)
}

function resetAll() {
  activeGroup.value = null
  activeParent.value = null
  activeCat.value = null
  store.saveNav(null, null)
}

function openBrands(cat) {
  activeCat.value = cat.id
  drawerCatId.value = cat.id
  drawerCat.value = cat
  drawerTitle.value = cat.name
  drawerVisible.value = true
  store.fetchBrands(cat.id)
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN')
}

async function triggerCrawl() {
  if (!drawerCatId.value || crawling.value) return
  crawling.value = true
  try {
    await api.triggerCategory(drawerCatId.value)
    ElMessage.success('爬取已触发，数据将在几秒内更新')
    store.clearBrandsCache(drawerCatId.value)
    // 轮询等待爬取完成，最多等 30 秒
    let retries = 0
    const poll = setInterval(async () => {
      retries++
      store.clearBrandsCache(drawerCatId.value)
      await store.fetchBrands(drawerCatId.value)
      const brands = store.brandsCache[drawerCatId.value]
      if ((brands && brands.length > 0) || retries >= 6) {
        clearInterval(poll)
        crawling.value = false
        if (brands && brands.length > 0) {
          brandTableKey.value++
          // 刷新 groups，更新小类卡片的品牌数
          await store.fetchGroups()
          ElMessage.success(`爬取完成，获取到 ${brands.length} 个品牌`)
        } else {
          ElMessage.warning('爬取完成，暂无数据（可能该类别尚未被网站收录）')
        }
      }
    }, 5000)
  } catch (e) {
    crawling.value = false
    ElMessage.error(e.message || '触发爬取失败')
  }
}

watch(() => store.searchKeyword, () => {
  activeGroup.value = null
  activeParent.value = null
  activeCat.value = null
})
</script>

<style scoped>
.group-list { margin-top: 12px; }

/* ── 面包屑 ── */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 2px;
  font-size: 13px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.bc-item { color: #606266; }
.bc-link { color: #5c6bc0; cursor: pointer; }
.bc-link:hover { text-decoration: underline; }
.bc-current { font-weight: 600; color: #1a1a2e; }
.bc-sep { color: #c0c4cc; }

/* ── 大类网格 ── */
.group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}
.group-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: #fff;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.18s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border: 2px solid transparent;
  -webkit-tap-highlight-color: transparent;
}
.group-card:hover, .group-card:active {
  border-color: #5c6bc0;
  box-shadow: 0 4px 12px rgba(92,107,192,0.15);
}
.group-icon { font-size: 20px; flex-shrink: 0; }
.group-card-name { font-size: 13px; font-weight: 600; color: #1a1a2e; flex: 1; min-width: 0; }
.group-card-count {
  font-size: 11px;
  background: #e8eaf6;
  color: #5c6bc0;
  padding: 2px 6px;
  border-radius: 10px;
  white-space: nowrap;
  flex-shrink: 0;
}
.group-card.ungrouped { opacity: 0.55; border-style: dashed; }
.group-card.ungrouped:hover { opacity: 1; }

/* ── 中类网格 ── */
.parent-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.parent-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  background: #fff;
  border: 2px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  -webkit-tap-highlight-color: transparent;
}
.parent-card:hover, .parent-card:active { border-color: #7986cb; }
.parent-card-name { font-size: 14px; font-weight: 500; color: #303133; }
.parent-card-count {
  font-size: 11px;
  background: #e8eaf6;
  color: #5c6bc0;
  padding: 1px 6px;
  border-radius: 8px;
}

/* ── 小类网格 ── */
.cat-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.cat-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #fff;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  -webkit-tap-highlight-color: transparent;
}
.cat-card:hover, .cat-card:active { border-color: #a5d6a7; }
.cat-card.active { border-color: #43a047; background: #f1f8e9; }
.cat-card.no-data { opacity: 0.45; }
.cat-card-name { font-size: 13px; font-weight: 500; color: #303133; }

/* ── 抽屉标题 ── */
.drawer-header { display: flex; flex-direction: column; gap: 4px; }
.drawer-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.drawer-title { font-size: 17px; font-weight: 700; color: #1a1a2e; }
.drawer-meta { display: flex; align-items: center; gap: 8px; margin-top: 2px; flex-wrap: wrap; }
.meta-path { font-size: 12px; color: #909399; }

/* ── 移动端适配 ── */
@media (max-width: 640px) {
  .group-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  .group-card { padding: 10px 12px; border-radius: 10px; }
  .group-icon { font-size: 18px; }
  .group-card-name { font-size: 13px; }

  .parent-grid { gap: 6px; }
  .parent-card { padding: 8px 12px; }
  .parent-card-name { font-size: 13px; }

  .cat-grid { gap: 6px; }
  .cat-card { padding: 7px 10px; }
  .cat-card-name { font-size: 12px; }

  .breadcrumb { font-size: 12px; }
}
</style>
