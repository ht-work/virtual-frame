<template>
  <div class="right-part common-space">
    <div class="right-chart-item">
      <DeviceChart :config="vm" />
    </div>
    <div class="right-chart-item">
      <DeviceChart :config="bm" />
    </div>
    <div class="right-chart-item">
      <DeviceChart :config="pm" />
    </div>
  </div>
</template>

<script>
import DeviceChart from './device/OV_Device'

import Metric from '@/util/metric'
import Config from '@/util/api_config'

export default {
  name: 'OV_RightCharts',
  components: {
    DeviceChart
  },
  data () {
    let obj = {
      vm: {
        deviceType: '云主机',
        usage: this.getUsage_VM(),
        metricConfig: this.getMetricConfig_VM()
      },
      bm: {
        deviceType: '裸金属',
        usage: this.getUsage_BM(),
        metricConfig: this.getMetricConfig_BM()
      },
      pm: {
        deviceType: 'KVM宿主机',
        usage: this.getUsage_PM(),
        metricConfig: this.getMetricConfig_PM()
      }
    }
    return obj
  },
  methods: {
    getSlideOption () {
      let swiperOption = {
        autoplay: {
          delay: Config.SwiperInterval
        }
      }
      return swiperOption
    },
    _getUsage (type) {
      let usage = {
        cpu: {
          type: type,
          title: 'CPU利用率',
          metrics: [Metric.name.device.cpu_usage_avg]
        },
        mem: {
          type: type,
          title: '内存利用率',
          metrics: [Metric.name.device.mem_usage_avg]
        }
      }
      return usage
    },
    getUsage_VM () {
      return this._getUsage('VM')
    },
    getUsage_BM () {
      return this._getUsage('BM')
    },
    getUsage_PM () {
      return this._getUsage('PM')
    },
    _getMetricConfig (type) {
      let metricObj = {
        busy: Metric.name.device.busy,
        health: Metric.name.device.health,
        ha: Metric.name.device.ha,
        unbalance: Metric.name.device.unbalance
      }
      let list = [
        {
          tooltip: 'device.busy',
          titleSuffix: 'Top3',
          title: '繁忙度',
          type: type,
          metrics: [metricObj.busy]
        },
        {
          tooltip: 'device.health',
          titleSuffix: 'Bottom3',
          title: '健康度',
          type: type,
          metrics: [metricObj.health]
        },
        {
          tooltip: 'device.ha',
          titleSuffix: 'Bottom3',
          title: '可用度',
          type: type,
          metrics: [metricObj.ha]
        },
        {
          tooltip: 'device.unbalance',
          titleSuffix: 'Top3',
          title: '不平衡度',
          type: type,
          metrics: [metricObj.unbalance]
        }
      ]

      let obj = {
        list: list,
        swiperOption: this.getSlideOption()
      }
      return obj
    },
    getMetricConfig_VM () {
      return this._getMetricConfig('VM')
    },
    getMetricConfig_BM () {
      return this._getMetricConfig('BM')
    },
    getMetricConfig_PM () {
      return this._getMetricConfig('PM')
    }
  }
}
</script>

<style lang="less">

</style>
