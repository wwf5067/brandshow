<template>
  <div class="brand-table-wrap">
    <el-skeleton :loading="loading" :rows="4" animated>
      <template #default>
        <el-empty v-if="!brands.length" description="暂无品牌数据" :image-size="60" />
        <el-table v-else :data="brands" size="small" stripe style="width: 100%">
          <el-table-column label="排名" width="70" align="center">
            <template #default="{ row }">
              <span :class="['rank-badge', `rank-${row.rank}`]">{{ row.rank }}</span>
            </template>
          </el-table-column>

          <el-table-column label="品牌" min-width="160">
            <template #default="{ row }">
              <div class="brand-cell">
                <el-avatar
                  v-if="row.logo_url"
                  :src="proxyLogo(row.logo_url)"
                  :size="32"
                  shape="square"
                  @error="() => true"
                />
                <div class="brand-info">
                  <a
                    v-if="row.detail_url"
                    :href="row.detail_url"
                    target="_blank"
                    class="brand-name"
                  >{{ row.name }}</a>
                  <span v-else class="brand-name">{{ row.name }}</span>
                  <span v-if="row.company_name" class="company-name">{{ row.company_name }}</span>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="排名变化" width="90" align="center">
            <template #default="{ row }">
              <template v-if="row.prev_rank && row.prev_rank !== row.rank">
                <el-tag
                  :type="row.rank < row.prev_rank ? 'success' : 'danger'"
                  size="small"
                >
                  {{ row.rank < row.prev_rank ? '↑' : '↓' }}
                  {{ Math.abs(row.prev_rank - row.rank) }}
                </el-tag>
              </template>
              <span v-else class="na">—</span>
            </template>
          </el-table-column>

          <el-table-column label="更新" width="80" align="center">
            <template #default="{ row }">
              <span class="time-text">{{ formatDate(row.updated_at) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-skeleton>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useCategoryStore } from '../stores/category'

const props = defineProps({ categoryId: { type: Number, required: true } })
const store = useCategoryStore()

const loading = computed(() => !!store.brandsLoading[props.categoryId])
const brands = computed(() => store.brandsCache[props.categoryId] || [])

// 展开时拉取数据；若返回空则轮询重试（覆盖爬取尚未完成的窗口期）
onMounted(async () => {
  await store.fetchBrands(props.categoryId)
  // 如果空，最多重试 4 次（每次间隔 5s），适用于刚触发爬取后立即展开的场景
  let retries = 0
  const poll = setInterval(async () => {
    if (brands.value.length > 0 || retries >= 4) {
      clearInterval(poll)
      return
    }
    retries++
    store.clearBrandsCache(props.categoryId)
    await store.fetchBrands(props.categoryId)
  }, 5000)
})

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

function proxyLogo(url) {
  if (!url) return ''
  // 将 img.chinapp.com 图片路由到本地代理，绕过防盗链
  return url.replace(/^https?:\/\/img\.chinapp\.com/, '/img-proxy')
}
</script>

<style scoped>
.brand-table-wrap { padding: 8px 0; }

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  font-weight: 700;
  font-size: 13px;
  background: #e8eaf6;
  color: #5c6bc0;
}
.rank-badge.rank-1 { background: #ffd700; color: #7a5c00; }
.rank-badge.rank-2 { background: #c0c0c0; color: #555; }
.rank-badge.rank-3 { background: #cd7f32; color: #fff; }

.brand-cell { display: flex; align-items: center; gap: 10px; }
.brand-info { display: flex; flex-direction: column; }

.brand-name {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  text-decoration: none;
}
.brand-name:hover { color: #409eff; }

.company-name {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.index-val { font-weight: 600; color: #e6a23c; }
.na { color: #c0c4cc; }
.time-text { font-size: 12px; color: #909399; }
</style>
