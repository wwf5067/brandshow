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
          <span>类别列表</span>
          <div class="cat-filters">
            <el-select
              v-model="catGroupFilter"
              placeholder="按大类筛选"
              size="small"
              clearable
              style="width:140px"
              @change="loadCategories(1)"
            >
              <el-option
                v-for="g in groupOptions"
                :key="g"
                :label="g"
                :value="g"
              />
            </el-select>
            <el-input
              v-model="catSearch"
              placeholder="搜索类别名"
              size="small"
              clearable
              style="width:180px"
              @input="debouncedSearch"
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
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="triggerOne(row.id)">爬取</el-button>
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
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { useCategoryStore } from '../stores/category'

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
const catPage = ref(1)
const catTotal = ref(0)
let searchTimer = null

// 大类选项（从已加载数据动态生成）
const groupOptions = computed(() => {
  const groups = new Set(categories.value.map(c => c.group_name).filter(Boolean))
  return [...groups].sort()
})

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

onMounted(() => {
  loadStatus()
  loadCategories()
  // 如果打开时正在爬取，自动开始轮询
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

.cat-filters { display: flex; gap: 8px; align-items: center; }
.cat-pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-gray { color: #c0c4cc; }
.text-secondary { color: #606266; font-size: 12px; }
</style>
