import Metric from '@/util/metric'
import CMDB from '@/util/cmdb'
import MixinCommon from '../Mixin_OV_Common'

let mixin = {
  mixins: [MixinCommon],
  methods: {
    // 过滤重复记录
    filterN (list, COUNT_NUM) {
      let res = []
      let obj = {}
      for (let i in list) {
        let item = list[i]
        let id = item.metric.app
        // 如果这个id还没有加入，并且不含有中文，那么就加入列表
        let containsChinese = /[\u4E00-\u9FA5]+/.test(id);
        if (!obj[id] && !containsChinese) {
          obj[id] = true
          res.push(item)
          if (res.length >= COUNT_NUM) {
            return res
          }
        }
      }
      return res
    },
    /*
    返回以下结构对象：
    list=[{id:xx, type='xx', info:{}, value:xx}]
    */
    handleQueryResponse (list) {
      //过滤剩下15个，再查询云主机和裸金属繁忙度
      list = this.filterN(list, 15)
      let resList = []
      for (let i in list) {
        let item = list[i]
        item.id = item.metric.app
        //"metric":{"__name__":"app_unbalance","app":"App1","rp":"huchi1","tenant":"IT","type":"BM"}
        //"values":[ [时间,值],[时间，值] ]
        item.info = item.metric
        item.type = 'app'
        item.value = this.convertValue(item.value[1])
        delete item.metric
        resList.push(item)
      }
      return resList
    },
    handleSpecialQuery (metricName, query) {
      if (metricName === Metric.name.app.busy) {
        query = 'topk(5,' + query + ')'
      }
      return query
    },
    formatCMDBData (entry) {
      entry.id = entry.owner_biz_system
      entry.name = entry.owner_biz_system_bizSystem_name
    },
    // 合并cmdb数据和指标数据
    mergeMetricWithCMDB (resObj, metricData) {
      let cmdbObj = {}
      let cmdbData = resObj.cmdb
      for (let i = 0; i < cmdbData.length; i++) {
        this.formatCMDBData(cmdbData[i])
        cmdbObj[cmdbData[i].id] = cmdbData[i]
      }
      let resourceBusyObj = {}
      let resourceBusyData = resObj.resource_busy
      for (let j = 0; j < resourceBusyData.length; j++) {
        let item = resourceBusyData[j]
        resourceBusyObj[item.id] = resourceBusyObj[item.id] || {}
        resourceBusyObj[item.id][item.info.type] = item.value
      }
      let retMetricData = []
      //最初查出繁忙度top25，经过过滤剩下15个，在查出云主机和裸金属繁忙度，如果有没数据的过滤掉，最后取5个
      let count = 0;
      for (let j in metricData) {
        if(count >= 5){
          break;
        }
        
        let entry = metricData[j]
        let id = entry.id
        entry.cmdb = cmdbObj[id]
        entry.resourceBusy = resourceBusyObj[id]
        if(typeof(entry.resourceBusy) == 'undefined' || (typeof(entry.resourceBusy.VM) == 'undefined' && typeof(entry.resourceBusy.BM) == 'undefined')){
          console.log("Get resource busy undefined. Ignore: " + JSON.stringify(entry.cmdb))
          continue;
        }
        // TODO: filter undefined cmdb
        if (entry.cmdb) {
          retMetricData.push(metricData[j])
          count++
        }
      }
      return retMetricData
    },
    buildSpecialQueries (baseMetricList) {
      let qs = []
      let result = []
      let types = ['BM', 'VM']
      for (let i in baseMetricList){
        let currentMetric = baseMetricList[i];
        let appId = currentMetric.info.app;
        let tenantId = currentMetric.info.tenant;
        let rpId = currentMetric.info.rp;
        let currentQuery = this.idsQueryMetrics[0] + '{app="' + appId + '",tenant="' + tenantId + '",rp="' + rpId + '",type=~"' + types.join('|') + '"}'
        qs.push(currentQuery)
      }
      //let query = this.idsQueryMetrics[0] + '{app=~"' + ids.join('|') + '",type=~"' + types.join('|') + '"}'
      result.push(qs.join(' or '))
      console.log("query data result:" + result[0])
      return result
    },
    buildTopNData (baseMetricList, cb) {
      // 构造查询
      let qs = this.buildSpecialQueries(baseMetricList)
      console.log(JSON.stringify(qs))

      let count = 0
      let resObj = {}
      let TASK_COUNT = 2
      let self = this

      let done = function () {
        let newList = self.mergeMetricWithCMDB(resObj, baseMetricList)
        cb && cb(newList)
      }
      Metric.querySingle(qs[0], function (data) {
        resObj.resource_busy = self.handleQueryResponse(data)
        count++
        if (count === TASK_COUNT) {
          done && done()
        }
      })

      let ids = baseMetricList.map(function (item) {
          return item.id
      })
      CMDB.getAppsByIds(ids, function (cmdbList) {
        if (cmdbList && cmdbList.data) {
          cmdbList = cmdbList.data
        }
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
      // 获取前20条记录，最后再过滤
      let query = 'topk(25,' + this.metrics[0] + ')'
      let queries = [query]
      let TASK_COUNT = queries.length
      let count = 0
      let resList = []
      let done = function () {
        let metricList = self.handleQueryResponse(resList)
        // let ids = metricList.map(function (item) {
        //   return item.id
        // })
        // ids.sort()
        self.buildTopNData(metricList, cb)
      }
      let func = function (query, callback) {
        // 查询top5
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
