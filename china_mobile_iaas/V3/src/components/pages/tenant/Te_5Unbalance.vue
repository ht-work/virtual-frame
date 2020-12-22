<template>
  <div class="rank-container main-trend">
    <div class="lc2-header">
      <span>{{title}}趋势</span>
      <span v-tooltip='getTip("tenant.unbalance")' class="info-tooltip"></span>
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
    let unba = '不平衡度'
    let obj = {
      title: unba,
      chartId: Metric.name.tenant.unbalance,
      type: 'tenant',
      chartConfig: {
        title: unba,
        yTitle: unba,
        legends: [unba, '裸金属', '云主机']
      },
      dateRangeConfig: null,
      itemId: this.$route.query.id, // get from router
      chartOpt: null,
      metrics: [Metric.name.tenant.unbalance, Metric.name.tenant.resource_unbalance]
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
