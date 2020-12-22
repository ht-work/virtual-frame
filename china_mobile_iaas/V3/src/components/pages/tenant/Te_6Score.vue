<template>
  <div class="rank-container main-trend">
    <div class="lc2-header">
      <span>{{title}}趋势</span>
      <span v-tooltip='getTip("tenant.score")' class="info-tooltip"></span>
    </div>
    <LineChart :dom-id="chartId" :option="chartOpt" class="chart-area" />
  </div>
</template>

<script>
import Mixin from '@/components/mixin/Mixin'
import MixinLine from './Mixin_Te_Line'
import Metric from '@/util/metric'
import LineChart from '@/components/common/echarts/LineChart'

export default {
  name: 'LeftChart2',
  mixins: [Mixin, MixinLine],
  components: {
    LineChart
  },
  data () {
    let name = '租户评分'
    let obj = {
      title: name,
      chartId: Metric.name.tenant.score_avg_replace,
      type: 'tenant',
      chartConfig: {
        title: name,
        yTitle: name,
        legends: [name],
        hideLegend: true
      },
      dateRangeConfig: null,
      itemId: this.$route.query.id, // get from router
      chartOpt: null,
      metrics: [Metric.name.tenant.score_avg_replace]
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
