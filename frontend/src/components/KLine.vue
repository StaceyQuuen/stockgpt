<template>
  <div ref="chart" style="width: 100%; height: 400px;"></div>
</template>

<script setup>
import * as echarts from "echarts"
import { onMounted, ref } from "vue"

const chart = ref(null)

onMounted(() => {

  const myChart = echarts.init(chart.value)

  const option = {

    title: { text: "Stock Price" },

    xAxis: {
      type: "category",
      data: ["Mon", "Tue", "Wed", "Thu", "Fri"]
    },

    yAxis: { type: "value" },

    series: [
      {
        type: "line",
        data: [120, 132, 101, 134, 90]
      }
    ]
  }

  myChart.setOption(option)
})
</script>