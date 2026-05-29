<template>
  <div class="admin">
    <h2 class="page-title">管理后台</h2>

    <!-- Status Card -->
    <el-card class="status-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>爬虫状态</span>
          <el-button size="small" :loading="refreshing" @click="loadStatus">刷新</el-button>
        </div>
      </template>
      <el-skeleton :loading="!status" :rows="3" animated>
        <template #default>
          <el-descriptions v-if="status" :column="3" border>
            <el-descriptions-item label="大类数">{{ status.total_groups }}</el-descriptions-item>
            <el-descriptions-item label="中类数">{{ status.total_parents }}</el-descriptions-item>
            <el-descriptions-item label="小类数">{{ status.total_categories }}</el-descriptions-item>
            <el-descriptions-item label="品牌总数">{{ status.total_brands }}</el-descriptions-item>
            <el-descriptions-item label="今日已爬">{{ status.crawled_today }}</el-descriptions-item>
            <el-descriptions-item label="运行状态">
              <el-tag :type="status.is_running ? 'warning' : 'success'">
                {{ status.is_running ? '运行中' : '空闲' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="上次发现" :span="3">
              {{ status.last_discovery_at || '从未' }}
            </el-descriptions-item>
          </el-descriptions>
        </template>
      </el-skeleton>
    </el-card>

    <!-- Actions Card -->
    <el-card class="actions-card" shadow="never">
      <template #header>操作</template>
      <div class="actions">
        <div class="action-item">
          <div class="action-desc">
            <strong>发现类别</strong>
            <p>从 chinapp.com 首页爬取并发现所有品牌类别，首次使用必须先执行。</p>
          </div>
          <el-button type="primary" :loading="discovering" @click="doDiscover">
            开始发现
          </el-button>
        </div>

        <el-divider />

        <div class="action-item">
          <div class="action-desc">
            <strong>重新分配本周调度</strong>
            <p>将所有类别随机分配到本周7天，立即生效。</p>
          </div>
          <el-button type="warning" :loading="scheduling" @click="doSchedule">
            重新分配
          </el-button>
        </div>

        <el-divider />

        <div class="action-item">
          <div class="action-desc">
            <strong>手动触发单个类别</strong>
            <p>输入类别 ID 立即触发该类别的品牌爬取。</p>
          </div>
          <div class="trigger-row">
            <el-input-number v-model="triggerCatId" :min="1" placeholder="类别 ID" style="width:140px" />
            <el-button type="success" :loading="triggering" @click="doTrigger">触发</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Category List with Trigger buttons -->
    <el-card class="cats-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>类别列表 <span class="cat-total">共 {{ catTotal }} 条</span></span>
          <div class="cat-filters">
            <!-- 大类 -->
            <el-select
              v-model="catGroupFilter"
              placeholder="大类"
              size="small"
              clearable
              style="width:120px"
              @change="onGroupChange"
            >
              <el-option v-for="g in allGroups" :key="g" :label="g" :value="g" />
            </el-select>
            <!-- 中类（随大类联动） -->
            <el-select
              v-model="catParentFilter"
              placeholder="中类"
              size="small"
              clearable
              :disabled="!catGroupFilter"
              style="width:120px"
              @change="loadCategories(1)"
            >
              <el-option v-for="p in currentParents" :key="p" :label="p" :value="p" />
            </el-select>
            <!-- 搜索 -->
            <el-input
              v-model="catSearch"
              placeholder="搜索类别名"
              size="small"
              clearable
              style="width:160px"
              @input="debouncedSearch"
              @clear="loadCategories(1)"
            />
          </div>
        </div>
      </template>
      <el-table :data="categories" v-loading="catLoading" size="small" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="类别名" min-width="120" />
        <el-table-column label="大类" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.group_name" size="small" effect="plain" type="primary">
              {{ row.group_name }}
            </el-tag>
            <span v-else class="text-gray">—</span>
          </template>
        </el-table-column>
        <el-table-column label="中类" width="110">
          <template #default="{ row }">
            <span v-if="row.parent_name" class="text-secondary">{{ row.parent_name }}</span>
            <span v-else class="text-gray">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="brand_count" label="品牌数" width="80" align="center" />
        <el-table-column label="上次爬取" width="110">
          <template #default="{ row }">
            <span :class="row.last_crawled_at ? '' : 'text-gray'">
              {{ row.last_crawled_at ? new Date(row.last_crawled_at).toLocaleDateString('zh-CN') : '未爬取' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="下次计划" width="120">
          <template #default="{ row }">
            <span class="text-gray">
              {{ row.next_crawl_at ? new Date(row.next_crawl_at).toLocaleString('zh-CN', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}) : '—' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="triggerOne(row.id)">爬取</el-button>
            <el-button size="small" plain @click="viewCategory(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="cat-pagination">
        <el-pagination
          v-model:current-page="catPage"
          :page-size="20"
          :total="catTotal"
          layout="prev, pager, next"
          background
          small
          @current-change="loadCategories"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { useCategoryStore } from '../stores/category'

const router = useRouter()
const categoryStore = useCategoryStore()

const status = ref(null)
const refreshing = ref(false)
const discovering = ref(false)
const scheduling = ref(false)
const triggering = ref(false)
const triggerCatId = ref(null)

const categories = ref([])
const catLoading = ref(false)
const catSearch = ref('')
const catGroupFilter = ref('')
const catParentFilter = ref('')
const catPage = ref(1)
const catTotal = ref(0)
let searchTimer = null

// 全量大类/中类（从 /meta 接口获取，不依赖当前页数据）
const allGroups = ref([])
const allParents = ref({})  // { group_name: [parent_name, ...] }

const currentParents = computed(() =>
  catGroupFilter.value ? (allParents.value[catGroupFilter.value] || []) : []
)

async function loadMeta() {
  try {
    const res = await api.getCategoriesMeta()
    allGroups.value = res.groups
    allParents.value = res.parents
  } catch {}
}

function onGroupChange() {
  catParentFilter.value = ''
  loadCategories(1)
}

async function loadStatus() {
  refreshing.value = true
  try {
    status.value = await api.getCrawlerStatus()
  } finally {
    refreshing.value = false
  }
}

async function loadCategories(page = catPage.value) {
  catLoading.value = true
  catPage.value = page
  try {
    const res = await api.getCategories({
      search: catSearch.value,
      group_name: catGroupFilter.value,
      parent_name: catParentFilter.value,
      page,
      page_size: 20,
    })
    categories.value = res.items
    catTotal.value = res.total
  } finally {
    catLoading.value = false
  }
}

function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadCategories(1), 300)
}

// 轮询：触发爬取后每 3 秒刷新状态，直到 is_running=false
let pollTimer = null
function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    await loadStatus()
    if (!status.value?.is_running) {
      stopPolling()
      loadCategories()  // 爬完后刷新列表
      ElMessage.success('爬取完成')
    }
  }, 3000)
}
function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function doDiscover() {
  discovering.value = true
  try {
    const res = await api.triggerDiscover()
    ElMessage.success(res.message || '发现任务已启动')
    setTimeout(() => { loadStatus(); startPolling() }, 1000)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    discovering.value = false
  }
}

async function doSchedule() {
  scheduling.value = true
  try {
    const res = await api.triggerWeeklySchedule()
    ElMessage.success(res.message || '调度已重新分配')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    scheduling.value = false
  }
}

async function doTrigger() {
  if (!triggerCatId.value) return ElMessage.warning('请输入类别 ID')
  triggering.value = true
  try {
    const res = await api.triggerCategory(triggerCatId.value)
    ElMessage.success(res.message || '爬取已触发')
    categoryStore.clearBrandsCache(triggerCatId.value)
    setTimeout(startPolling, 1000)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    triggering.value = false
  }
}

async function triggerOne(id) {
  try {
    const res = await api.triggerCategory(id)
    ElMessage.success(res.message || '爬取已触发')
    categoryStore.clearBrandsCache(id)
    setTimeout(startPolling, 1000)
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function viewCategory(row) {
  // 保存导航状态，跳转到首页展示该小类的品牌排行
  categoryStore.saveNav(row.group_name, row.parent_name || '__none__')
  // 同时触发品牌数据加载和抽屉打开
  categoryStore.clearBrandsCache(row.id)
  router.push({ path: '/', query: { catId: row.id, catName: row.name } })
}

onMounted(() => {
  loadStatus()
  loadCategories()
  loadMeta()
  if (status.value?.is_running) startPolling()
})
</script>

<style scoped>
.admin { padding-bottom: 48px; }
.page-title { font-size: 22px; font-weight: 700; margin-bottom: 20px; color: #1a1a2e; }

.status-card, .actions-card, .cats-card { margin-bottom: 20px; border-radius: 10px; }

.card-header { display: flex; align-items: center; justify-content: space-between; }

.actions { padding: 4px 0; }

.action-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}

.action-desc strong { font-size: 14px; }
.action-desc p { font-size: 12px; color: #909399; margin-top: 4px; }

.trigger-row { display: flex; gap: 8px; align-items: center; }

.cat-filters { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.cat-total { font-size: 12px; color: #909399; font-weight: 400; margin-left: 4px; }
.cat-pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-gray { color: #c0c4cc; }
.text-secondary { color: #606266; font-size: 12px; }
</style>
