<template>
  <div class="search-bar">
    <el-input
      v-model="keyword"
      :placeholder="placeholder"
      clearable
      size="large"
      @input="onInput"
      @clear="onClear"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  placeholder: { type: String, default: '搜索品牌类别，如：手机、电视、洗衣机…' },
  debounce: { type: Number, default: 300 },
})

const emit = defineEmits(['search'])
const keyword = ref('')
let timer = null

function onInput(val) {
  clearTimeout(timer)
  timer = setTimeout(() => emit('search', val), props.debounce)
}

function onClear() {
  clearTimeout(timer)
  emit('search', '')
}
</script>

<style scoped>
.search-bar {
  max-width: 600px;
}
</style>
