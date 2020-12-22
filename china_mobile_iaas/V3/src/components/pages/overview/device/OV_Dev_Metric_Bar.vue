<template>
  <div class="ov-health-container">
    <div class="chart-title">
      <span>{{title}}{{titleSuffix}}</span>
      <span v-tooltip="getTip(tooltip)" class="info-tooltip"></span>
    </div>
    <BarChart :dom-id="chartId" :option="chartOpt" class="chart-area" />
  </div>
</template>

<script>
import MixinBar from './Mixin_OV_Dev_Metric_Bar'
import MixinTimer from '@/components/mixin/Mixin_Vue_Timer'
import BarChart from '@/components/common/echarts/EchartsChart'

export default {
  name: 'LeftChart2',
  mixins: [MixinTimer, MixinBar],
  components: {
    BarChart
  },
  props: ['config'],
  data () {
    let obj = {
      metricDataList: null,
      chartOpt: null
    }
    let chartId = this.config.metrics[0] + '_' + this.config.type
    for (let key in this.config) {
      obj[key] = this.config[key]
    }
    obj.chartId = chartId
    return obj
  }
}
</script>

<style lang="less" scoped>
.ov-health-container{
  width: 100%;
  height: 100%;
  .chart-title{
    display: inline-flex;
    align-items: center;
    margin-left: 10px;
  }
  .chart-area{
    height: 100%;
    min-height: 140px;
  }
}
</style>
