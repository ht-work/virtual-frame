<template>
  <div class="ov-health-container">
    <div class="busy-container">
      <span>健康度Bottom5</span>
      <span v-tooltip='getTip("app.health")' class="info-tooltip"></span>
    </div>
    <BarChart :dom-id="chartId" :option="chartOpt" class="chart-area" />
  </div>
</template>

<script>
import MixinBar from './Mixin_OV_App_Bar'
import MixinTimer from '@/components/mixin/Mixin_Vue_Timer'
import Metric from '@/util/metric'
import BarChart from '@/components/common/echarts/BarChart'

export default {
  name: 'LeftChart2',
  mixins: [MixinTimer, MixinBar],
  components: {
    BarChart
  },
  data () {
    let obj = {
      chartId: Metric.name.app.health,
      chartOpt: null,
      chartConfig: {
        title: '健康度Bottom5业务系统'
      },
      // ,
      // headers: ['名称', '不平衡度', 'CPU利用率', '内存利用率'],
      // items: [],
      // type: 'tenant',
      // itemId: this.$route.query.id, // get from router
      metrics: [Metric.name.app.health]
    }
    return obj
  }
}
</script>

<style lang="less" scoped>
.ov-health-container{
  width: 100%;
  height: 100%;
  .chart-area{
    width: 100%;
    height: 100%;
    min-height: 200px;
  }
}
</style>
<style lang="less">
.busy-container{
  display: flex;
  align-items: center;
  margin: 10px 0 0 10px;
}
</style>
