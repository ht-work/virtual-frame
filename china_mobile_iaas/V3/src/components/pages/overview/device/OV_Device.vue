<template>
  <div class="server-container">
    <div class="lc2-header">{{deviceType}}</div>
    <div class="usage-container">
      <DeviceUsage :usage="usage" />
    </div>
    <div class="metrics-ranking">
      <DeviceMetrics :metricConfig="metricConfig"  />
    </div>
  </div>
</template>

<script>
import DeviceUsage from './OV_Dev_Usage'
import DeviceMetrics from './OV_De_Metrics'

export default {
  name: 'LeftChart2',
  props: ['config'],
  components: {
    DeviceUsage,
    DeviceMetrics
  },
  computed: {
    deviceType () {
      return this.config && this.config.deviceType
    },
    usage () {
      return this.config && this.config.usage
    },
    metricConfig () {
      return this.config && this.config.metricConfig
    }
  }
}
</script>

<style lang="less" scoped>
.server-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  height: 100%;
  .metrics-ranking {
    width: 100%;
    margin-top: -10px;
  }
}
</style>
