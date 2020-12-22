<template>
  <div class="rank-container main-trend">
    <div class="lc2-header">
      <span>{{title}}趋势</span>
      <span v-tooltip='getTip("app.busy")' class="info-tooltip"></span>
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
      title: '繁忙度',
      chartId: Metric.name.app.busy,
      type: 'app',
      chartConfig: {
        title: '繁忙度',
        yTitle: '繁忙度',
        legends: ['总体', '裸金属', '云主机']
      },
      dateRangeConfig: null,
      itemId: this.$route.query.id, // get from router
      chartOpt: null,
      metrics: [Metric.name.app.resource_busy, Metric.name.app.busy]
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
