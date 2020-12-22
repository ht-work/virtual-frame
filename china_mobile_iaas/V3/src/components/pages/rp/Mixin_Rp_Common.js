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
    /**
     * 构造查询表达式
     * @param metric
     * @param conditionObj: 支持两种格式：{app:'123'} 以及 {app: {operator:'=~', v: '123|234'}}
     * @returns {*}
     */
    getMetricQuery (metric, conditionObj) {
      let q = metric
      // 构造查询： metricName{id="13"}
      if (conditionObj && Object.keys(conditionObj).length > 0) {
        q += '{'
        let i = 0
        let keyLen = Object.keys(conditionObj).length
        for (let k in conditionObj) {
          if (conditionObj[k] && conditionObj[k].operator && conditionObj[k].v) {
            q += k + conditionObj[k].operator + '"' + conditionObj[k].v + '"'
          } else {
            // simple case
            q += k + '="' + conditionObj[k] + '"'
          }
          i++
          if (keyLen > 1 && (i !== keyLen)) {
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
