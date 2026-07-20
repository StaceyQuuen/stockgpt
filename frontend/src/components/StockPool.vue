<template>
  <!-- Overlay -->
  <Teleport to="body">
    <Transition name="drawer-fade">
      <div v-if="visible" class="drawer-overlay" @click.self="$emit('close')">
        <Transition name="drawer-slide">
          <div v-if="visible" class="drawer-panel">
            <!-- Header -->
            <div class="drawer-header">
              <h2 class="drawer-title">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                  <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
                </svg>
                短线股票池
              </h2>
              <div class="drawer-actions">
                <button class="refresh-btn" @click="fetchPool" :disabled="loading">
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"
                       :class="{ spinning: loading }">
                    <polyline points="23 4 23 10 17 10"/>
                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                  </svg>
                  {{ loading ? '扫描中...' : '刷新' }}
                </button>
                <button class="close-btn" @click="$emit('close')" title="关闭">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>

            <!-- Market Status -->
            <div v-if="marketInfo" class="market-bar">
              <span class="market-label">大盘环境</span>
              <span class="market-score" :class="marketClass">{{ marketInfo.market_score }}/10</span>
              <span class="market-detail">{{ marketInfo.market_detail }}</span>
            </div>

            <!-- Error -->
            <div v-if="error" class="pool-error">{{ error }}</div>

            <!-- Empty -->
            <div v-else-if="!loading && stocks.length === 0" class="pool-empty">
              {{ poolData?.error || '暂无数据，请点击刷新按钮扫描' }}
            </div>

            <!-- Stock List -->
            <div v-if="stocks.length > 0" class="stock-list">
              <div
                v-for="(stock, idx) in stocks"
                :key="stock.code"
                class="stock-item"
                :class="{ expanded: expandedCode === stock.code }"
                @click="toggleExpand(stock)"
              >
                <!-- Main Row -->
                <div class="stock-row">
                  <span class="rank">{{ idx + 1 }}</span>
                  <div class="stock-main">
                    <div class="stock-name-row">
                      <span class="stock-star">{{ stock.star }}</span>
                      <span class="stock-name">{{ stock.name }}</span>
                      <span class="stock-code">{{ stock.code }}</span>
                    </div>
                  </div>
                  <div class="stock-score-area">
                    <span class="score-num" :class="scoreClass(stock.total_score)">{{ stock.total_score }}</span>
                    <span class="score-label">分</span>
                  </div>
                  <div class="stock-right">
                    <span class="stock-price">{{ stock.price.toFixed(2) }}</span>
                    <span class="stock-chg" :class="stock.change_pct >= 0 ? 'chg-up' : 'chg-down'">
                      {{ stock.change_pct >= 0 ? '+' : '' }}{{ stock.change_pct.toFixed(2) }}%
                    </span>
                  </div>
                </div>

                <!-- Expanded Detail -->
                <div v-if="expandedCode === stock.code" class="stock-detail">
                  <div class="dim-grid">
                    <div class="dim-item" v-for="dim in dimensions" :key="dim.key">
                      <span class="dim-label">{{ dim.label }}</span>
                      <div class="dim-bar-bg">
                        <div class="dim-bar" :style="{ width: dimPct(stock.scores[dim.key], dim.max) + '%' }"
                             :class="barClass(stock.scores[dim.key], dim.max)"></div>
                      </div>
                      <span class="dim-val">{{ stock.scores[dim.key] }}/{{ dim.max }}</span>
                    </div>
                  </div>
                  <button class="analyze-btn" @click.stop="doSelect(stock)">
                    详细分析此股 →
                  </button>
                </div>
              </div>
            </div>

            <!-- Loading -->
            <div v-if="loading" class="pool-loading">
              <span class="spinner"></span>
              正在扫描全市场（约 1-2 分钟）...
            </div>

            <!-- Footer -->
            <div v-if="scanTime && !loading" class="pool-footer">
              <span>{{ scanTime }}</span>
              <span>共扫描 {{ totalScanned }} 只 · 8 维度打分</span>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue"
import { getStockPool } from "../api/stock"

const props = defineProps({ visible: Boolean })
const emit = defineEmits(["close", "select"])

const poolData = ref(null)
const loading = ref(false)
const error = ref("")
const expandedCode = ref(null)
const hasLoaded = ref(false)

const dimensions = [
  { key: "market", label: "市场环境", max: 10 },
  { key: "sector", label: "热点板块", max: 15 },
  { key: "trend", label: "趋势", max: 20 },
  { key: "volume", label: "成交量", max: 15 },
  { key: "breakout", label: "突破形态", max: 15 },
  { key: "capital", label: "资金流", max: 10 },
  { key: "turnover", label: "换手率", max: 5 },
  { key: "risk_reward", label: "盈亏比", max: 10 },
]

const stocks = computed(() => poolData.value?.stocks || [])
const scanTime = computed(() => poolData.value?.scan_time || "")
const totalScanned = computed(() => poolData.value?.total_scanned || 0)
const marketInfo = computed(() => poolData.value ? {
  market_score: poolData.value.market_score,
  market_detail: poolData.value.market_detail,
} : null)

const marketClass = computed(() => {
  const s = poolData.value?.market_score || 0
  if (s >= 7) return "market-good"
  if (s >= 4) return "market-mid"
  return "market-bad"
})

function scoreClass(score) {
  if (score >= 80) return "score-excellent"
  if (score >= 60) return "score-good"
  if (score >= 40) return "score-mid"
  return "score-low"
}

function dimPct(val, max) {
  return max > 0 ? (val / max) * 100 : 0
}

function barClass(val, max) {
  const pct = val / max
  if (pct >= 0.7) return "bar-high"
  if (pct >= 0.4) return "bar-mid"
  return "bar-low"
}

function toggleExpand(stock) {
  expandedCode.value = expandedCode.value === stock.code ? null : stock.code
}

function doSelect(stock) {
  emit("select", { code: stock.code, name: stock.name })
  emit("close")
}

// Auto-fetch on first open
watch(() => props.visible, (v) => {
  if (v && !hasLoaded.value) {
    fetchPool()
    hasLoaded.value = true
  }
})

async function fetchPool() {
  loading.value = true
  error.value = ""
  expandedCode.value = null
  try {
    const data = await getStockPool()
    poolData.value = data
    if (data.error && !data.stocks?.length) {
      error.value = data.error
    }
  } catch (e) {
    error.value = "获取股票池失败：" + (e.message || "网络错误")
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Overlay + Drawer */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}
.drawer-panel {
  width: 420px;
  max-width: 92vw;
  height: 100%;
  background: var(--bg-page, #0f1117);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 20px;
  box-shadow: -8px 0 30px rgba(0,0,0,0.3);
}

/* Transitions */
.drawer-fade-enter-active,
.drawer-fade-leave-active { transition: opacity 0.25s ease; }
.drawer-fade-enter-from,
.drawer-fade-leave-to { opacity: 0; }

.drawer-slide-enter-active { transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.drawer-slide-leave-active { transition: transform 0.2s ease-in; }
.drawer-slide-enter-from,
.drawer-slide-leave-to { transform: translateX(100%); }

/* Header */
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  flex-shrink: 0;
}
.drawer-title {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  margin: 0;
}
.drawer-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
.refresh-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  font-size: 12px;
  color: var(--text-muted);
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}
.refresh-btn:hover:not(:disabled) { color: var(--accent); border-color: var(--accent); }
.refresh-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px; height: 32px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s;
}
.close-btn:hover { color: var(--text-primary); background: var(--bg-input); }

.spinning { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Market bar */
.market-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 12px;
  background: var(--bg-input);
  border-radius: 8px;
  font-size: 12px;
  flex-shrink: 0;
}
.market-label { color: var(--text-muted); font-weight: 500; flex-shrink: 0; }
.market-score {
  font-weight: 700;
  font-size: 13px;
  padding: 1px 8px;
  border-radius: 10px;
  flex-shrink: 0;
}
.market-good { background: rgba(34,197,94,0.15); color: var(--success); }
.market-mid { background: rgba(234,179,8,0.15); color: #eab308; }
.market-bad { background: rgba(239,68,68,0.12); color: var(--danger); }
.market-detail { color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Stock list */
.stock-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}
.stock-item {
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  overflow: hidden;
}
.stock-item:hover { background: var(--bg-input); }
.stock-item.expanded { background: var(--bg-input); }

.stock-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 10px;
}
.rank {
  width: 20px;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  flex-shrink: 0;
}
.stock-main { flex: 1; min-width: 0; }
.stock-name-row { display: flex; align-items: center; gap: 6px; }
.stock-star { font-size: 10px; color: #eab308; letter-spacing: -1px; }
.stock-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.stock-code { font-size: 11px; font-family: var(--font-mono); color: var(--text-muted); }

/* Score */
.stock-score-area {
  display: flex;
  align-items: baseline;
  gap: 2px;
  flex-shrink: 0;
  margin-right: 4px;
}
.score-num { font-size: 18px; font-weight: 800; font-family: var(--font-mono); }
.score-label { font-size: 10px; color: var(--text-muted); }
.score-excellent { color: var(--success); }
.score-good { color: #22c55e; }
.score-mid { color: #eab308; }
.score-low { color: var(--text-muted); }

.stock-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 1px;
  flex-shrink: 0;
}
.stock-price { font-size: 13px; font-weight: 600; font-family: var(--font-mono); color: var(--text-primary); }
.stock-chg { font-size: 11px; font-family: var(--font-mono); font-weight: 500; }
.chg-up { color: var(--success); }
.chg-down { color: var(--danger); }

/* Expanded detail */
.stock-detail {
  padding: 4px 10px 14px 40px;
  animation: fadeUp 0.2s ease;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
.dim-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 16px;
}
@media (max-width: 420px) {
  .dim-grid { grid-template-columns: 1fr; }
}
.dim-item { display: flex; align-items: center; gap: 8px; }
.dim-label { font-size: 11px; color: var(--text-muted); width: 56px; flex-shrink: 0; }
.dim-bar-bg {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 3px;
  overflow: hidden;
}
.dim-bar { height: 100%; border-radius: 3px; transition: width 0.3s ease; }
.bar-high { background: var(--success); }
.bar-mid { background: #eab308; }
.bar-low { background: rgba(255,255,255,0.15); }
.dim-val {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  width: 32px;
  text-align: right;
  flex-shrink: 0;
}

.analyze-btn {
  margin-top: 12px;
  padding: 7px 18px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  background: var(--accent);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  width: 100%;
}
.analyze-btn:hover { background: var(--accent-hover); }

/* States */
.pool-error, .pool-empty {
  padding: 24px;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}
.pool-error { color: var(--danger); }
.pool-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 28px;
  font-size: 13px;
  color: var(--text-muted);
}
.spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.2);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

/* Footer */
.pool-footer {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  margin-top: auto;
  border-top: 1px solid var(--border-color);
  font-size: 11px;
  color: var(--text-muted);
  flex-shrink: 0;
}
</style>
