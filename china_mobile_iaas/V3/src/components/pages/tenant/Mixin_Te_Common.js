import APIConfig from '@/util/api_config'

let mixin = {
  mounted () {
    this.initTimer && this.initTimer(APIConfig.RefreshInterval)
    this.loadData()
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
      let addedStr = "";
      if (conditionObj && Object.keys(conditionObj).length > 0) {
        addedStr += '{'
        let i = 0
        let keyLen = Object.keys(conditionObj).length
        for (let k in conditionObj) {
          if (conditionObj[k] && conditionObj[k].operator && conditionObj[k].v) {
            addedStr += k + conditionObj[k].operator + '"' + conditionObj[k].v + '"'
          } else {
            // simple case
            addedStr += k + '="' + conditionObj[k] + '"'
          }
          i++
          if (keyLen > 1 && (i !== keyLen)) {
            addedStr += ','
          }
        }
        addedStr += '}'
        if (q.indexOf("{#}") >= 0){
          //如果包含indexOf，则说明需要替换，而不是拼接
          return q.replace("{#}", addedStr);
        }else{
          return q + addedStr;
        }
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
