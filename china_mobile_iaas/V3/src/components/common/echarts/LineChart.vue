<template>
  <div :id="domId" class="line-chart-container"></div>
</template>

<script>
import echarts from 'echarts'
export default {
  name: 'LineChart',
  props: ['domId', 'option'],
  computed: {
    line () {
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
      if (this.line && this.option) {
        this.line.setOption(this.option, true)
      }
    }
  },
  watch: {
    option: {
      handler (newV, oldV) {
        this.line && this.line.setOption(newV, true)
      },
      deep: true
    }
  }
}
</script>

<style lang="less">
.line-chart-container{
  width: 100%;
  height: calc(100% - 30px);
}
</style>
