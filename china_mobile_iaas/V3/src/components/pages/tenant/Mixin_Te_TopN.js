import Metric from '@/util/metric'
import CMDB from '@/util/cmdb'
import MixinCommon from './Mixin_Te_Common'

let mixin = {
  mixins: [MixinCommon],
  methods: {
    /*
    返回以下结构对象：
    list=[{id:xx, type='xx', info:{}, value:xx}]
    */
    handleQueryResponse (list, idField, resourceType) {
      let resList = []
      for (let i in list) {
        let item = list[i]
        item.id = item.metric[idField]
        // "metric":{"__name__":"app_unbalance","app":"App1","rp":"huchi1","tenant":"IT","type":"BM"}
        // "values":[ [时间,值],[时间，值] ]
        item.info = item.metric
        item.type = resourceType
        item.value = this.convertValue(item.value[1])
        delete item.metric
        resList.push(item)
      }
      return resList
    },
    handleSpecialQuery (metricName, query) {
      if (metricName === Metric.name.app.unbalance) {
        query = 'topk(20,' + query + ')'
      }
      return query
    },
    // 合并cmdb数据和指标数据
    mergeMetricWithCMDB (resObj, metricData) {
      //console.log("start to merge metric with cmdb");
      // console.log("resObj", resObj);
      // console.log("metricData", metricData);
      let cmdbObj = {}
      let cmdbData = resObj.cmdb.data
      //console.log("cmdbData", cmdbData);
      let cpuData = resObj.cpu
      //console.log("cpuData", cpuData);
      let cpuObj = {}
      let memData = resObj.mem
      //console.log("memData", memData);
      let memObj = {}
      //console.log("start to loop");
      for (let i = 0; i < cmdbData.length; i++) {
        // console.log("cmdbData[i]", cmdbData[i]);
        // console.log("cpuData[i]", cpuData[i]);
        // console.log("memData[i]", memData[i]);
        // console.log("cmdbData[i].id", cmdbData[i].id);
        // console.log("cpuData[i].id", cpuData[i].id);
        // console.log("memData[i].id", memData[i].id);
        if(typeof(cmdbData[i]) != 'undefined' && typeof(cmdbData[i].id) != 'undefined'){
          cmdbObj[cmdbData[i].id] = cmdbData[i]
        }
        if(typeof(cpuData[i]) != 'undefined' && typeof(cpuData[i].id) != 'undefined'){
          cpuObj[cpuData[i].id] = cpuData[i]
        }
        if(typeof(memData[i]) != 'undefined' && typeof(memData[i].id) != 'undefined'){
          memObj[memData[i].id] = memData[i]
        }
        // console.log("cmdbObj", cmdbObj);
        // console.log("cpuObj", cpuObj);
        // console.log("memObj", memObj);
      }
      for (let j in metricData) {
        let entry = metricData[j]
        let id = entry.id
        //console.log("start to get id " + id);
        entry.cmdb = cmdbObj[id]
        if(typeof(cpuObj[id]) != 'undefined'){
          entry.cpu = cpuObj[id].value
        }else{
          console.log("cpu obj not find value. id: " + id);
        }
        if(typeof(memObj[id]) != 'undefined'){
          entry.mem = memObj[id].value
        }else{
          console.log("cpu obj not find value. id: " + id);
        }
      }
      //console.log("final metric data: ", metricData);
      //整理数据，取前5
      let finalData = new Array();
      let count = 0;
      for (let i in metricData){
        if(count >= 5){
          break;
        }
        let currentData = metricData[i];
        if(typeof(currentData) == 'undefined' || typeof(currentData.cmdb) == 'undefined'){
          continue;
        }
        finalData.push(currentData);
        count++;
      }
      //console.log("final data: " + JSON.stringify(finalData))
      return finalData;
    },
    buildSpecialQueries (ids) {
      let qs = []
      let confObj = {}
      // app_cpu_usage_avg{tenant="xx", app=~"xx|xx|xx|xx|xx"}
      confObj[this.type] = this.itemId
      confObj.app = {
        operator: '=~',
        v: ids.join('|')
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
      let TASK_COUNT = 3
      let self = this

      let done = function () {
        let newList = self.mergeMetricWithCMDB(resObj, baseMetricList)
        cb && cb(newList)
      }

      Metric.querySingle(qs[0], function (data) {
        resObj.cpu = self.handleQueryResponse(data, 'app', 'app')
        count++
        if (count === TASK_COUNT) {
          done && done()
        }
      })

      Metric.querySingle(qs[1], function (data) {
        resObj.mem = self.handleQueryResponse(data, 'app', 'app')
        count++
        if (count === TASK_COUNT) {
          done && done()
        }
      })

      CMDB.getAppsByIds(ids, function (cmdbList) {
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
        let metricList = self.handleQueryResponse(resList, 'app')
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
