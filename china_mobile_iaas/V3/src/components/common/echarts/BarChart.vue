<template>
  <div :id="domId" class="bar-chart-container"></div>
</template>

<script>
import echarts from 'echarts'
export default {
  name: 'BarChart',
  props: ['domId', 'option'],
  computed: {
    bar () {
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
      if (this.bar && this.option) {
        this.bar.setOption(this.option, true)
      }
    }
  },
  watch: {
    option: {
      handler (newV, oldV) {
        this.bar && this.bar.setOption(newV, true)
      },
      deep: true
    }
  }
}
</script>

<style lang="less">
.bar-chart-container{
  width: 100%;
  //height: calc(100% - 30px);
  height: 100%;
}
</style>
