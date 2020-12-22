import APIConfig from '@/util/api_config'

let mixin = {
  mounted () {
    this.loadData()
    this.initTimer(APIConfig.RefreshInterval)
    if (this.specialInit) {
      this.specialInit()
    }
  },
  methods: {
    convertValue (v) {
      v = parseFloat(v).toFixed(8)
      v = parseFloat(v).toFixed(2)
      return v
    },
    getMetricQuery (metric, conditionObj) {
      let q = metric
      // 构造查询： metricName{id="13"}
      if (conditionObj && Object.keys(conditionObj).length > 0) {
        q += '{'
        let i = 0
        for (let k in conditionObj) {
          q += k + '="' + conditionObj[k] + '"'
          i++
          if (i > 1) {
            q += ','
          }
        }
        q += '}'
        return q
      } else {
        return q
      }
    },
    getQueries () {
      let qs = []
      let confObj = {}
      confObj[this.type] = this.itemId
      for (let i = 0; i < this.metrics.length; i++) {
        let query = this.getMetricQuery(this.metrics[i], confObj)
        if (this.handleSpecialQuery) {
          query = this.handleSpecialQuery(this.metrics[i], query)
        }
        qs.push(query)
      }
      return qs
    },
    loadData () {
      let self = this
      this.getMetric(function (data) {
        self.handleMetricData && self.handleMetricData(data)
      })
    }
  }
}

export default mixin
