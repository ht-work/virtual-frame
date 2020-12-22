<template>
  <div class="center-chart">
    <div class="lc2-header">
      <span class="rp-title">资源池概况</span>
    </div>
    <div class="cc-main-container">
      <MainChart />
    </div>
  </div>
</template>

<script>
import MainChart from './OV_ResourcePool'
import Mixin from '@/components/mixin/Mixin'
export default {
  name: 'CenterCmp',
  mixins: [Mixin],
  components: {
    MainChart
  }
}
</script>

<style lang="less">
.center-chart {
  width: 100%;
  height: 100%;

  .cc-main-container {
    position: relative;
    width: 100%;
    height: 90%;
  }
}
</style>
