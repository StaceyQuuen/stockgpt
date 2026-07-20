import axios from "axios"

const API_BASE = "http://127.0.0.1:8080"

// ========== 短线分析（流式） ==========

export function streamShortTermAnalyze(data, onMessage) {
  const xhr = new XMLHttpRequest()
  xhr.open("POST", `${API_BASE}/api/v1/short-term-analyze`)
  xhr.setRequestHeader("Content-Type", "application/json")
  xhr.onprogress = function () {
    onMessage(xhr.responseText)
  }
  xhr.send(JSON.stringify(data))
}

// ========== 股票搜索 ==========

export async function searchStock(query) {
  const resp = await axios.get(`${API_BASE}/api/v1/stock/search`, {
    params: { q: query },
  })
  return resp.data
}

// ========== 股票池 ==========

export async function getStockPool() {
  const resp = await axios.get(`${API_BASE}/api/v1/stock-pool`)
  return resp.data
}
