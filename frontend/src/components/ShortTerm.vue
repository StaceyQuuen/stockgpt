<template>
  <div class="app">
    <!-- ===== Header ===== -->
    <header class="header">
      <div class="header-inner">
        <div class="logo">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
          <span class="logo-text">StockGPT</span>
        </div>
        <span class="header-tag">短线适配性分析</span>
      </div>
    </header>

    <main class="main">
      <!-- ===== 搜索区 ===== -->
      <section class="search-card">
        <h1 class="search-title">这只股票适合短线吗？</h1>
        <p class="search-sub">输入股票代码或名称，AI 多维度分析后给出评估</p>
        <div class="search-row">
          <div class="search-box">
            <StockSearch
              v-model="stockCode"
              placeholder="搜索股票代码或名称，如 601127、茅台"
              @select="onStockSelect"
            />
          </div>
          <button
            class="search-btn"
            @click="startAnalysis"
            :disabled="analyzing || !stockCode.trim()"
          >
            <template v-if="analyzing">
              <span class="spinner"></span>
              分析中
            </template>
            <template v-else>
              开始分析
            </template>
          </button>
        </div>
        <div v-if="selectedStock" class="selected-chip">
          <span>{{ selectedStock.name }}</span>
          <span class="chip-code">{{ selectedStock.code }}</span>
          <button class="chip-close" @click="clearSelection">&times;</button>
        </div>
      </section>

      <!-- ===== 股票池抽屉 ===== -->
      <StockPool :visible="poolOpen" @close="poolOpen = false" @select="onPoolSelect" />

      <!-- ===== 分析进度 ===== -->
      <section v-if="analyzing || analysisDone" class="card">
        <h2 class="card-title">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
          分析进度
        </h2>
        <div class="steps">
          <div
            v-for="(step, idx) in steps"
            :key="idx"
            class="step"
            :class="{ done: step.status === 'done', active: step.status === 'active' }"
          >
            <div class="step-dot">
              <template v-if="step.status === 'done'">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
              </template>
              <template v-else-if="step.status === 'active'">
                <span class="pulse"></span>
              </template>
              <template v-else>
                <span class="dot-idle">{{ idx + 1 }}</span>
              </template>
            </div>
            <span class="step-label">{{ step.label }}</span>
            <span v-if="step.status === 'active'" class="step-badge">进行中</span>
            <div v-if="idx < steps.length - 1" class="step-line" :class="{ filled: step.status === 'done' }"></div>
          </div>
        </div>
      </section>

      <!-- ===== 评估结果 ===== -->
      <section v-if="assessment" class="card assess-card">
        <h2 class="card-title">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          短线评估
        </h2>

        <div class="assess-grid">
          <!-- 评分圆 -->
          <div class="score-area">
            <div class="score-ring" :class="assessment.suitable ? 'ring-good' : 'ring-bad'">
              <span class="score-num">{{ assessment.score }}</span>
              <span class="score-unit">/100</span>
            </div>
            <div class="verdict" :class="assessment.suitable ? 'v-good' : 'v-bad'">
              {{ assessment.suitable ? '适合短线操作' : '不适合短线操作' }}
            </div>
          </div>

          <!-- 依据 -->
          <div class="reasons-area">
            <h3>判断依据</h3>
            <ul class="reason-list">
              <li v-for="(r, i) in assessment.reasons" :key="i">
                <span class="reason-dot"></span>
                {{ r }}
              </li>
            </ul>
          </div>
        </div>

        <!-- 持仓策略 -->
        <div v-if="assessment.suitable && assessment.strategy" class="strategy">
          <h3>持仓策略</h3>
          <div class="strategy-grid">
            <div class="s-item">
              <span class="s-label">入场区间</span>
              <span class="s-value">{{ assessment.strategy.entry_range || '待定' }}</span>
            </div>
            <div class="s-item">
              <span class="s-label">止盈位</span>
              <span class="s-value s-profit">{{ assessment.strategy.stop_profit || '待定' }}</span>
            </div>
            <div class="s-item">
              <span class="s-label">止损位</span>
              <span class="s-value s-loss">{{ assessment.strategy.stop_loss || '待定' }}</span>
            </div>
            <div class="s-item">
              <span class="s-label">建议仓位</span>
              <span class="s-value">{{ assessment.strategy.position_ratio || '待定' }}</span>
            </div>
            <div class="s-item">
              <span class="s-label">预期持仓</span>
              <span class="s-value">{{ assessment.strategy.hold_days || '待定' }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ===== 完整报告 ===== -->
      <section v-if="fullReport" class="card report-card">
        <h2 class="card-title">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          完整分析报告
        </h2>
        <div class="report-body" v-html="renderReport(fullReport)"></div>
      </section>

      <!-- ===== 原始输出 ===== -->
      <details v-if="rawOutput" class="card raw-card">
        <summary class="raw-summary">查看原始输出</summary>
        <pre class="raw-body">{{ rawOutput }}</pre>
      </details>

      <!-- ===== 免责声明 ===== -->
      <div class="disclaimer">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        以上分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。
      </div>
    </main>

    <!-- FAB: 股票池 -->
    <button class="pool-fab" :class="{ active: poolOpen }" @click="poolOpen = !poolOpen" title="短线股票池">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from "vue"
import StockSearch from "./StockSearch.vue"
import StockPool from "./StockPool.vue"
import { streamShortTermAnalyze } from "../api/stock"

const stockCode = ref("")
const selectedStock = ref(null)
const analyzing = ref(false)
const analysisDone = ref(false)
const rawOutput = ref("")
const assessment = ref(null)
const fullReport = ref("")
const progressEvents = ref([])
const poolOpen = ref(false)

// 进度步骤映射
const STEPS = [
  { name: "financial", label: "获取财务数据" },
  { name: "news", label: "新闻情绪分析" },
  { name: "technical", label: "技术指标计算" },
  { name: "risk", label: "风险评估" },
  { name: "short_term", label: "短线适配评估" },
  { name: "report", label: "生成报告" },
]

const completedSteps = computed(() => {
  const set = new Set()
  for (const evt of progressEvents.value) {
    for (const s of STEPS) {
      if (evt.includes(`${s.name} 节点启动`)) set.add(`${s.name}_start`)
      if (evt.includes("财务分析完成") && s.name === "financial") set.add(s.name)
      if (evt.includes("新闻分析完成") && s.name === "news") set.add(s.name)
      if (evt.includes("技术分析完成") && s.name === "technical") set.add(s.name)
      if (evt.includes("风险分析完成") && s.name === "risk") set.add(s.name)
      if (evt.includes("短线评估完成") && s.name === "short_term") set.add(s.name)
      if (evt.includes("报告生成完成") && s.name === "report") set.add(s.name)
    }
  }
  return set
})

const steps = computed(() =>
  STEPS.map((s) => {
    if (completedSteps.value.has(s.name)) return { ...s, status: "done" }
    if (completedSteps.value.has(`${s.name}_start`)) return { ...s, status: "active" }
    return { ...s, status: "pending" }
  })
)

function onStockSelect(item) {
  selectedStock.value = item
  stockCode.value = item.code
}

function clearSelection() {
  selectedStock.value = null
  stockCode.value = ""
}

function onPoolSelect(item) {
  selectedStock.value = item
  stockCode.value = item.code
  poolOpen.value = false
  startAnalysis()
}

function startAnalysis() {
  // 提取纯股票代码（可能格式："300199" 或 "300199 某某名称"）
  const code = stockCode.value.trim().split(/\s+/)[0]
  if (!code) return

  analyzing.value = true
  analysisDone.value = false
  progressEvents.value = []
  assessment.value = null
  fullReport.value = ""
  rawOutput.value = ""

  streamShortTermAnalyze(
    { stock_code: code, question: "分析这只股票是否适合短线操作" },
    (msg) => {
      rawOutput.value = msg
      parseStreamOutput(msg)
    }
  )

  setTimeout(() => {
    analyzing.value = false
  }, 180000)
}

function parseStreamOutput(text) {
  const lines = text.split("\n")
  const markers = ["▶️", "💰", "📰", "📈", "⚠️", "🎯", "📝", "📊"]
  for (const line of lines) {
    if (markers.some((m) => line.startsWith(m))) {
      if (!progressEvents.value.includes(line)) {
        progressEvents.value = [...progressEvents.value, line]
      }
    }
  }

  // 解析评估区块
  const assessMatch = text.match(
    /========== SHORT-TERM ASSESSMENT ==========\n([\s\S]*?)(?=========== FINAL REPORT|$)/
  )
  if (assessMatch) parseAssessmentBlock(assessMatch[1])

  // 解析完整报告
  const reportMatch = text.match(
    /========== FINAL REPORT ==========\n([\s\S]*?)(?=\n\[|$)/
  )
  if (reportMatch) {
    fullReport.value = reportMatch[1].trim()
    analyzing.value = false
    analysisDone.value = true
  }
}

function parseAssessmentBlock(block) {
  const scoreMatch = block.match(/评分:\s*(\d+)/)
  const suitableMatch = block.match(/适合短线:\s*✅\s*是/)
  const reasons = []
  const reasonLines = block.match(/•\s*(.+)/g)
  if (reasonLines) {
    for (const line of reasonLines) {
      reasons.push(line.replace(/•\s*/, "").trim())
    }
  }

  const strategy = {}
  const entryMatch = block.match(/入场区间:\s*(.+)/)
  const profitMatch = block.match(/止盈位:\s*(.+)/)
  const lossMatch = block.match(/止损位:\s*(.+)/)
  const posMatch = block.match(/建议仓位:\s*(.+)/)
  const holdMatch = block.match(/预期持仓:\s*(.+)/)

  if (entryMatch) strategy.entry_range = entryMatch[1].trim()
  if (profitMatch) strategy.stop_profit = profitMatch[1].trim()
  if (lossMatch) strategy.stop_loss = lossMatch[1].trim()
  if (posMatch) strategy.position_ratio = posMatch[1].trim()
  if (holdMatch) strategy.hold_days = holdMatch[1].trim()

  assessment.value = {
    score: scoreMatch ? parseInt(scoreMatch[1]) : 0,
    suitable: !!suitableMatch,
    reasons,
    strategy: Object.keys(strategy).length > 0 ? strategy : null,
  }
}

function renderReport(text) {
  return text
    .replace(/###\s+(.+)/g, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^- (.+)/gm, '<span class="rli">$1</span>')
    .replace(/\n{2,}/g, "<br/><br/>")
    .replace(/\n/g, "<br/>")
}
</script>

<style scoped>
/* ===== Layout ===== */
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.header {
  border-bottom: 1px solid var(--border-color);
  padding: 0 24px;
  background: rgba(15, 17, 23, 0.85);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 50;
}
.header-inner {
  max-width: 720px;
  margin: 0 auto;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--accent);
}
.logo-text {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.3px;
  color: var(--text-primary);
}
.header-tag {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(99, 102, 241, 0.12);
  color: var(--accent);
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.main {
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
  padding: 28px 20px 60px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ===== Search Card ===== */
.search-card {
  padding: 28px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
}
.search-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 4px;
  color: var(--text-primary);
}
.search-sub {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 18px;
}
.search-row {
  display: flex;
  gap: 10px;
  align-items: stretch;
}
.search-box {
  flex: 1;
}
.search-btn {
  padding: 0 28px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.2s, opacity 0.2s;
}
.search-btn:hover:not(:disabled) { background: var(--accent-hover); }
.search-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.selected-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 4px 10px 4px 12px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 20px;
  font-size: 13px;
  color: var(--text-primary);
}
.chip-code {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
}
.chip-close {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 16px;
  cursor: pointer;
  padding: 0 2px;
  line-height: 1;
}
.chip-close:hover { color: var(--text-primary); }

/* ===== Cards ===== */
.card {
  padding: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  animation: fadeUp 0.3s ease;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
}
.card-title svg { flex-shrink: 0; }

/* ===== Progress Steps ===== */
.steps {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.step {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  position: relative;
}
.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--bg-input);
  border: 2px solid var(--border-color);
  transition: all 0.3s;
}
.step.done .step-dot {
  background: var(--success);
  border-color: var(--success);
  color: #fff;
}
.step.active .step-dot {
  background: var(--accent);
  border-color: var(--accent);
}
.step-line {
  position: absolute;
  left: 13px;
  top: 38px;
  width: 2px;
  height: calc(100% - 18px);
  background: var(--border-color);
}
.step-line.filled {
  background: var(--success);
}
.step-label {
  font-size: 14px;
  color: var(--text-muted);
  transition: color 0.2s;
}
.step.done .step-label { color: var(--text-primary); }
.step.active .step-label { color: var(--text-primary); font-weight: 500; }
.step-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(99, 102, 241, 0.15);
  color: var(--accent);
}
.dot-idle { font-size: 11px; color: var(--text-muted); }

.pulse {
  width: 8px; height: 8px;
  background: #fff;
  border-radius: 50%;
  animation: pulsate 1.2s ease-in-out infinite;
}
@keyframes pulsate {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.7); }
}

/* ===== Assessment ===== */
.assess-grid {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}
@media (max-width: 520px) {
  .assess-grid { flex-direction: column; }
}
.score-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
.score-ring {
  width: 96px; height: 96px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 4px solid transparent;
  animation: ringIn 0.5s ease;
}
@keyframes ringIn {
  from { transform: scale(0.6); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.ring-good {
  background: rgba(34, 197, 94, 0.08);
  border-color: var(--success);
}
.ring-bad {
  background: rgba(239, 68, 68, 0.08);
  border-color: var(--danger);
}
.score-num {
  font-size: 32px;
  font-weight: 800;
  line-height: 1;
}
.ring-good .score-num { color: var(--success); }
.ring-bad .score-num { color: var(--danger); }
.score-unit {
  font-size: 12px;
  color: var(--text-muted);
}
.verdict {
  font-size: 14px;
  font-weight: 600;
  text-align: center;
}
.v-good { color: var(--success); }
.v-bad { color: var(--danger); }

.reasons-area {
  flex: 1;
  min-width: 0;
}
.reasons-area h3 {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
  margin-bottom: 10px;
}
.reason-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.reason-list li {
  font-size: 14px;
  color: var(--text-primary);
  display: flex;
  align-items: flex-start;
  gap: 10px;
  line-height: 1.5;
}
.reason-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--accent);
  flex-shrink: 0;
  margin-top: 7px;
}

/* ===== Strategy ===== */
.strategy {
  margin-top: 22px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}
.strategy h3 {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
  margin-bottom: 14px;
}
.strategy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.s-item {
  padding: 14px 16px;
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
}
.s-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.s-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.s-profit { color: var(--success); }
.s-loss { color: var(--danger); }

/* ===== Report ===== */
.report-body {
  font-size: 14px;
  line-height: 1.85;
  color: var(--text-secondary);
}
.report-body :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 20px 0 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border-color);
}
.report-body :deep(h3:first-child) { margin-top: 0; }
.report-body :deep(strong) {
  color: var(--text-primary);
}
.report-body :deep(.rli) {
  display: block;
  padding: 3px 0 3px 16px;
  position: relative;
}
.report-body :deep(.rli::before) {
  content: "•";
  position: absolute;
  left: 4px;
  color: var(--accent);
}

/* ===== Raw Output ===== */
.raw-card {
  padding: 0;
  overflow: hidden;
}
.raw-summary {
  padding: 14px 20px;
  font-size: 13px;
  color: var(--text-muted);
  cursor: pointer;
  user-select: none;
}
.raw-summary:hover { color: var(--text-secondary); }
.raw-body {
  margin: 0;
  padding: 16px 20px;
  background: #0a0b10;
  color: #6ee7b7;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  max-height: 320px;
  overflow: auto;
  white-space: pre-wrap;
  border-top: 1px solid var(--border-color);
}

/* ===== Disclaimer ===== */
.disclaimer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
  padding: 8px 0;
}

/* ===== Pool FAB ===== */
.pool-fab {
  position: fixed;
  right: 24px;
  bottom: 28px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35);
  transition: all 0.25s;
  z-index: 900;
}
.pool-fab:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 24px rgba(99, 102, 241, 0.5);
}
.pool-fab.active {
  background: var(--accent-hover);
  transform: scale(0.92);
}
</style>
