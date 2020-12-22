import Metric from '@/util/metric'

let mixin = {
  methods: {
    getStep (startDate, endDate) {
      let start = Metric.getTime(startDate)
      let end = Metric.getTime(endDate)
      // 默认为1个小时，1小时以内，则为默认采点间隔
      let range = 12 * Metric.defaultStep
      let minus = end - start
      let step = Metric.defaultStep
      // 超过1小时，则计算采点间隔
      if (minus > range) {
        step = minus / Metric.pointerNumber
      }
      return step
    }
  }
}

export default mixin
