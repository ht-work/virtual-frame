import Metric from '@/util/metric'
import CMDB from '@/util/cmdb'
import MixinCommon from './Mixin_Rp_Common'

let mixin = {
  mixins: [MixinCommon],
  methods: {
    /*
    返回以下结构对象：
    list=[{id:xx, type='xx', info:{}, value:xx}]
    */
    handleQueryResponse (list) {
      let resList = []
      for (let i in list) {
        let item = list[i]
        item.id = item.metric.tenant
        // "metric":{"__name__":"te_resource_quota","rp":"huchi1","tenant":"IT","type":"VCPU"}
        // "values":[ [时间,值],[时间，值] ]
        item.info = item.metric
        item.type = item.metric && item.metric.type
        item.value = this.convertValue(item.value[1])
        delete item.metric
        resList.push(item)
      }
      return resList
    },
    handleSpecialQuery (metricName, query) {
      if (metricName === Metric.name.tenant.quota_sum) {
        query = 'topk(5,' + query + ')'
      }
      return query
    },
    // 合并cmdb数据和指标数据
    mergeMetricWithCMDB (resObj, metricData) {
      let cmdbObj = {}
      let cmdbData = resObj.cmdb.data
      for (let i = 0; i < cmdbData.length; i++) {
        cmdbObj[cmdbData[i].id] = cmdbData[i]
      }
      let quotaData = resObj.resourceQuota
      let cpuQuotaObj = {}
      let memQuotaObj = {}
      for (let i = 0; i < quotaData.length; i++) {
        // type1: {id1:value, id2:value2}, type2: {id1: value, id2: value2}
        let item = quotaData[i]
        if (item.type === 'VCPU') {
          cpuQuotaObj[item.id] = item.value
        } else if (item.type === 'MEM') {
          memQuotaObj[item.id] = item.value
        }
      }
      for (let j in metricData) {
        let entry = metricData[j]
        let id = entry.id
        entry.cmdb = cmdbObj[id]
        entry.cpu = cpuQuotaObj[id]
        entry.mem = memQuotaObj[id]
      }
      return metricData
    },
    buildSpecialQueries (ids) {
      let qs = []
      let confObj = {}
      // app_cpu_usage_avg{tenant="xx", app=~"xx|xx|xx|xx|xx"}
      confObj[this.type] = this.itemId
      confObj.tenant = {
        operator: '=~',
        v: ids.join('|')
      }
      let types = ['VCPU', 'MEM']
      confObj.type = {
        operator: '=~',
        v: types.join('|')
      }
      for (let i = 0; i < this.idsQueryMetrics.length; i++) {
        let query = this.getMetricQuery(this.idsQueryMetrics[i], confObj)
        qs.push(query)
      }
      return qs
    },
    buildTopNData (ids, baseMetricList, cb) {
      // 构造查询
      let qs = this.buildSpecialQueries(ids)

      let count = 0
      let resObj = {}
      let TASK_COUNT = 2
      let self = this

      let done = function () {
        let newList = self.mergeMetricWithCMDB(resObj, baseMetricList)
        cb && cb(newList)
      }

      Metric.querySingle(qs[0], function (data) {
        resObj.resourceQuota = self.handleQueryResponse(data)
        count++
        if (count === TASK_COUNT) {
          done && done()
        }
      })

      CMDB.getTenantsByIds(ids, function (cmdbList) {
        resObj.cmdb = cmdbList
        count++
        if (count === TASK_COUNT) {
          done && done()
        }
      })
    },
    /// 最终需要的数据
    /*
    此处的value即为unbalance数据
    列表：list: [{info:{}, value:xx, cpu:xx, mem:xx},{}]
    */
    getMetric (cb) {
      let self = this
      let queries = this.getQueries()
      let TASK_COUNT = queries.length
      let count = 0
      let resList = []
      let done = function () {
        let metricList = self.handleQueryResponse(resList)
        let ids = metricList.map(function (item) {
          return item.id
        })
        ids.sort()
        self.buildTopNData(ids, metricList, cb)
      }
      let func = function (query, callback) {
        // 查询top5的app不平衡业务系统
        Metric.querySingle(query, function (data) {
          resList = resList.concat(data)
          count++
          if (count === TASK_COUNT) {
            callback && callback()
          }
        })
      }
      for (let i = 0; i < TASK_COUNT; i++) {
        func(queries[i], done)
      }
    },
    handleMetricData (data) {
      this.items = data
    },
    refresh () {
      console.log('timer reaches and load data again')
      this.loadData()
    }
  }
}

export default mixin
