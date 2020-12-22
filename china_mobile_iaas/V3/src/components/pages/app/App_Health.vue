<template>
  <div class="rank-container main-trend">
    <div class="lc2-header">
      <span>{{title}}趋势</span>
      <span v-tooltip='getTip("app.health")' class="info-tooltip"></span>
    </div>
    <LineChart :dom-id="chartId" :option="chartOpt" class="chart-area" />
  </div>
</template>

<script>
import Mixin from '@/components/mixin/Mixin'
import MixinAppLine from './Mixin_App_Line'
import Metric from '@/util/metric'
import LineChart from '@/components/common/echarts/LineChart'

export default {
  name: 'LeftChart2',
  mixins: [Mixin, MixinAppLine],
  components: {
    LineChart
  },
  data () {
    let obj = {
      title: '健康度',
      chartId: Metric.name.app.health,
      type: 'app',
      chartConfig: {
        title: '健康度',
        yTitle: '健康度',
        legends: ['健康度'],
        hideLegend: true
      },
      dateRangeConfig: null,
      itemId: this.$route.query.id, // get from router
      chartOpt: null,
      metrics: [Metric.name.app.health]
    }
    return obj
  }
}
</script>

<style lang="less" scoped>
.rank-container {
  width: 100%;
  height: 100%;
}
</style>
