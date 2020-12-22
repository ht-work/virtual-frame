<template>
  <div class="ov-usage-container">
    <PieChart :dom-id="chartId" :option="chartOpt" class="chart-area" />
  </div>
</template>

<script>
import MixinPie from './Mixin_OV_Dev_Usage_Pie'
import MixinTimer from '@/components/mixin/Mixin_Vue_Timer'
import PieChart from '@/components/common/echarts/EchartsChart'

export default {
  name: 'LeftChart2',
  mixins: [MixinTimer, MixinPie],
  components: {
    PieChart
  },
  props: ['config'],
  data () {
    let chartId = this.config.metrics[0] + '_' + this.config.type
    let obj = {
      chartId: chartId,
      chartOpt: null,
      title: this.config && this.config.title,
      type: this.config && this.config.type,
      metrics: (this.config && this.config.metrics) || []
    }
    return obj
  }
}
</script>

<style lang="less" scoped>
.ov-usage-container{
  width: 100%;
  height: 100%;
  margin-left: -10px;
}
</style>
