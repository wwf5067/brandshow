<template>
  <svg
    v-if="points.length >= 2"
    :width="width"
    :height="height"
    class="sparkline"
    :aria-label="`排名趋势: ${trendLabel}`"
  >
    <!-- trend line -->
    <polyline
      :points="pointsStr"
      fill="none"
      :stroke="lineColor"
      stroke-width="1.5"
      stroke-linejoin="round"
      stroke-linecap="round"
    />
    <!-- latest dot -->
    <circle
      :cx="lastPt.x"
      :cy="lastPt.y"
      r="2.5"
      :fill="lineColor"
    />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  history: { type: Array, default: () => [] },  // [{rank, recorded_at}]
  width:   { type: Number, default: 80 },
  height:  { type: Number, default: 28 },
})

const MAX_RANK = 10
const PAD = 3

const points = computed(() => {
  if (!props.history || props.history.length < 2) return []
  const n = props.history.length
  return props.history.map((item, i) => {
    const x = PAD + (i / (n - 1)) * (props.width - PAD * 2)
    const rank = Math.max(1, Math.min(MAX_RANK, item.rank))
    // rank 1 → y small (top), rank 10 → y large (bottom)
    const y = PAD + ((rank - 1) / (MAX_RANK - 1)) * (props.height - PAD * 2)
    return { x, y }
  })
})

const pointsStr = computed(() =>
  points.value.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
)

const lastPt = computed(() => points.value[points.value.length - 1])

// trend: compare first vs last rank; lower rank number = better
const lineColor = computed(() => {
  const h = props.history
  if (h.length < 2) return '#5c6bc0'
  const first = h[0].rank
  const last  = h[h.length - 1].rank
  if (last < first) return '#67c23a'   // improved (green)
  if (last > first) return '#f56c6c'   // declined (red)
  return '#5c6bc0'                     // stable (indigo)
})

const trendLabel = computed(() => {
  const h = props.history
  if (h.length < 2) return '—'
  return `最新排名 ${h[h.length - 1].rank}`
})
</script>

<style scoped>
.sparkline { display: block; }
</style>
