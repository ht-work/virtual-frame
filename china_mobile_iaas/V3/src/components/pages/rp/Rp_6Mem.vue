<template>
  <div class="rank-container main-trend">
    <div class="lc2-header">
      <span>{{title}}趋势</span>
    </div>
    <LineChart :dom-id="chartId" :option="chartOpt" class="chart-area" />
  </div>
</template>

<script>
import Mixin from '@/components/mixin/Mixin'
import MixinLine from './Mixin_Rp_Line'
import Metric from '@/util/metric'
import LineChart from '@/components/common/echarts/LineChart'

export default {
  name: 'LeftChart2',
  mixins: [Mixin, MixinLine],
  components: {
    LineChart
  },
  data () {
    let name = '内存利用率'
    let obj = {
      title: name,
      chartId: Metric.name.rp.mem,
      type: 'rp',
      chartConfig: {
        title: name,
        yTitle: name,
        legends: ['裸金属', '云主机', 'KVM宿主机']
      },
      dateRangeConfig: null,
      itemId: this.$route.query.id, // get from router
      chartOpt: null,
      metrics: [Metric.name.rp.mem]
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
