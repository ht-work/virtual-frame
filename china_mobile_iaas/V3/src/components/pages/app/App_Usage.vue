<template>
    <div class="rank-container main-trend">
        <div class="lc2-header">
          <span>{{title}}趋势</span>
          <span v-tooltip='getTip("app.assign")' class="info-tooltip"></span>
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
      title: '使用率',
      chartId: Metric.name.app.resource_usage,
      type: 'app',
      chartConfig: {
        title: '资源使用率',
        yTitle: '使用率（%）',
        legends: ['裸金属', '云主机', 'vCPU', '内存']
      },
      dateRangeConfig: null,
      itemId: this.$route.query.id, // get from router
      chartOpt: null,
      metrics: [Metric.name.app.resource_usage]
    }
    return obj
  }
}
</script>

<style lang="less" scoped>
.rank-container {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>
