import Metric from '@/util/metric'
import CMDB from '@/util/cmdb'
import MixinAppCommon from './Mixin_App_Common'

let mixin = {
  mixins: [MixinAppCommon],
  methods: {
    /*
    返回以下结构对象：
    list=[{id:xx, type='device', info:{}, value:xx}]
    */
    handleQueryResponse (list) {
      let resList = []
      let resourceType = 'device'
      for (let i in list) {
        let item = list[i]
        item.id = item.metric.id
        // "metric":{"__name__":"app_resource_assign_ratio","app":"App1","rp":"huchi1","tenant":"IT","type":"BM"}
        // "values":[ [时间,值],[时间，值] ]
        item.info = item.metric
        item.type = resourceType // 此处返回的设备的id
        item.value = this.convertValue(item.value[1])
        delete item.metric
        resList.push(item)
      }
      return resList
    },
    handleSpecialQuery (metricName, query) {
      if (metricName === Metric.name.device.health) {
        query = 'bottomk(5,' + query + ')'
      }
      return query
    },
    // 合并cmdb数据和指标数据
    mergeMetricWithCMDB (cmdbData, metricData) {
      let cmdbObj = {}
      for (let i in cmdbData) {
        let item = cmdbData[i]
        cmdbObj[item.id] = item
      }
      for (let j in metricData) {
        let entry = metricData[j]
        entry.cmdb = cmdbObj[entry.id]
      }
      return metricData
    },
    /// 最终需要的数据
    /*
    列表：list: [{info:{}, value:xx},{}]
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
        CMDB.getDeviceByIds(ids, function (cmdbList) {
          let newList = self.mergeMetricWithCMDB(cmdbList, metricList)
          cb && cb(newList)
        })
      }
      let func = function (query, callback) {
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
