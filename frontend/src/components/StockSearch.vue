<template>
  <div class="stock-search">
    <input
      v-model="query"
      :placeholder="placeholder"
      @input="onInput"
      @focus="showDropdown = true"
      @blur="onBlur"
      class="search-input"
    />
    <div v-if="showDropdown && results.length" class="dropdown">
      <div
        v-for="item in results"
        :key="item.code"
        class="dropdown-item"
        @mousedown.prevent="onSelect(item)"
      >
        <span class="code">{{ item.code }}</span>
        <span class="name">{{ item.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { searchStock } from "../api/stock"

const emit = defineEmits(["select"])
const props = defineProps({
  placeholder: { type: String, default: "输入股票代码或名称" },
})

const query = ref("")
const results = ref([])
const showDropdown = ref(false)
let debounceTimer = null

function onInput() {
  clearTimeout(debounceTimer)
  if (!query.value.trim()) {
    results.value = []
    return
  }
  debounceTimer = setTimeout(async () => {
    try {
      results.value = await searchStock(query.value.trim())
      showDropdown.value = true
    } catch {
      results.value = []
    }
  }, 400)
}

function onSelect(item) {
  query.value = `${item.code} ${item.name}`
  showDropdown.value = false
  emit("select", item)
}

function onBlur() {
  // 延迟关闭，让 mousedown 先触发
  setTimeout(() => {
    showDropdown.value = false
  }, 200)
}
</script>

<style scoped>
.stock-search {
  position: relative;
  width: 100%;
}

.search-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #555;
  border-radius: 6px;
  background: #1e1e1e;
  color: #eee;
  font-size: 14px;
  box-sizing: border-box;
}

.search-input::placeholder {
  color: #888;
}

.search-input:focus {
  outline: none;
  border-color: #4f46e5;
}

.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  margin-top: 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
}

.dropdown-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  gap: 12px;
}

.dropdown-item:hover {
  background: #3a3a3a;
}

.code {
  color: #a78bfa;
  font-family: monospace;
}

.name {
  color: #ccc;
}
</style>
