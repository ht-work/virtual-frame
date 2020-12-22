<template>
  <div :id="domId" class="chart-container"></div>
</template>

<script>
import echarts from 'echarts'
export default {
  name: 'EchartsChart',
  props: ['domId', 'option'],
  computed: {
    chart () {
      if (this.domId) {
        return echarts.init(document.getElementById(this.domId))
      }
      return null
    }
  },
  mounted () {
    this.init()
  },
  methods: {
    init () {
      if (this.chart && this.option) {
        this.chart.setOption(this.option, true)
      }
    }
  },
  watch: {
    option: {
      handler (newV, oldV) {
        this.chart && this.chart.setOption(newV, true)
      },
      deep: true
    }
  }
}
</script>

<style lang="less">
.chart-container{
  width: 100%;
  height: 100%;
}
</style>
