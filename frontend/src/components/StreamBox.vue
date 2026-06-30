<template>
  <div class="container">

    <h2>📊 StockGPT AI 分析</h2>

    <input v-model="stockCode" placeholder="输入股票代码" />

    <input v-model="question" placeholder="输入问题" />

    <button @click="startAnalysis">开始分析</button>

    <div class="output">
      <pre>{{ output }}</pre>
    </div>

  </div>
</template>

<script setup>
import { ref } from "vue"
import { streamAnalyze } from "../api/stock"

const stockCode = ref("601127")
const question = ref("分析这只股票")
const output = ref("")

function startAnalysis() {

  output.value = ""

  streamAnalyze(
    {
      stock_code: stockCode.value,
      question: question.value
    },
    (msg) => {

      output.value = msg
    }
  )
}
</script>

<style>
.container {
  max-width: 600px;
  margin: 40px auto;
}

input {
  display: block;
  margin: 10px 0;
  padding: 8px;
  width: 100%;
}

button {
  padding: 10px;
  background: #4f46e5;
  color: white;
  border: none;
  cursor: pointer;
}

.output {
  margin-top: 20px;
  background: #111;
  color: #0f0;
  padding: 10px;
  height: 300px;
  overflow: auto;
}
</style>