<template>
    <div class="rank-container main-trend">
        <div class="lc2-header">
          <span>{{title}}趋势</span>
          <span v-tooltip='getTip("rp.assign")' class="info-tooltip"></span>
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
    let obj = {
      title: '分配率',
      chartId: Metric.name.rp.resource_assignRatio,
      type: 'rp',
      chartConfig: {
        title: '资源分配率',
        yTitle: '分配率（%）',
        legends: ['裸金属', 'vCPU', '内存']
      },
      dateRangeConfig: null,
      itemId: this.$route.query.id, // get from router
      chartOpt: null,
      metrics: [Metric.name.rp.resource_assignRatio]
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
