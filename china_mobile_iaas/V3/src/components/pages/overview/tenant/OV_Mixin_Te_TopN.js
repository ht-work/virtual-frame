import Metric from '@/util/metric'
import CMDB from '@/util/cmdb'
import MixinCommon from '../Mixin_OV_Common'
import MixinScoreLevel from '@/components/mixin/Mixin_Score_Level'

let mixin = {
  mixins: [MixinCommon, MixinScoreLevel],
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
        //"metric":{"__name__":"te_cpu","rp":"huchi1","tenant":"IT"}
        //"values":[ [时间,值] ]
        item.info = item.metric
        item.type = 'tenant'
        item.value = this.convertValue(item.value[1])
        item.value = Math.round(parseFloat(item.value))
        delete item.metric
        resList.push(item)
      }
      return resList
    },
    formatCMDBData (entry) {
      entry.name = entry.department2_orgName_name
    },
    // 合并cmdb数据和指标数据
    mergeMetricWithCMDB (resObj, metricData) {
      let cmdbObj = {}
      let cmdbData = resObj.cmdb.data
      for (let i = 0; i < cmdbData.length; i++) {
        this.formatCMDBData(cmdbData[i])
        cmdbObj[cmdbData[i].id] = cmdbData[i]
      }
      /*
      metricObj = {id1: {metric1:v1, metric2:v2}, id2: {metric1:v1, metric2:v2}}
       */

      let nameToKey = {
        "avg(te_assign_ratio{#}<=100) by (tenant)": "te_assign_ratio",
        "avg(te_cpu{#}<=100) by (tenant)": "te_cpu",
        "avg(te_mem{#}<=100) by (tenant)": "te_mem",
        "avg(te_busy{#} <= 99999999) by (tenant)": "te_busy",
        "avg(te_unbalance{#} <= 99999999) by (tenant)": "te_unbalance",
      };

      let metricObj = {}
      for (let i = 0; i < this.idsQueryMetrics.length; i++) {
        let name = this.idsQueryMetrics[i]
        let metricList = resObj[name]
        for (let j = 0; j < metricList.length; j++) {
          let item = metricList[j]
          metricObj[item.id] = metricObj[item.id] || {}
          let key = nameToKey[name]
          metricObj[item.id][key] = item.value
        }
      }

      for (let j in metricData) {
        let entry = metricData[j]
        let id = entry.id
        entry.cmdb = cmdbObj[id]
        entry.metric = metricObj[id]
        entry.level = this.getTenantLevel(entry.value)
      }
      return metricData
    },
    buildSpecialQueries (ids) {
      let qs = []
      let confObj = {}
      // te_cpu{tenant=~"xx|xx|xx|xx|xx"}
      confObj.tenant = {
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
      // 指标查询 + 配置查询
      let TASK_COUNT = qs.length + 1
      let self = this

      let done = function () {
        let newList = self.mergeMetricWithCMDB(resObj, baseMetricList)
        cb && cb(newList)
      }
      // 使用匿名函数，处理指标查询
      for (let i = 0; i < qs.length; i++) {
        (function (metricName, query) {
          console.log("start to query tenant topN, Query: ");
          console.log(query);
          Metric.querySingle(query, function (data) {
            console.log("get query result:");
            console.log(data);
            resObj[metricName] = self.handleQueryResponse(data)
            count++
            if (count === TASK_COUNT) {
              done && done()
            }
          })
        })(self.idsQueryMetrics[i], qs[i])
      }
      CMDB.getTenantsByIds(ids, function (cmdbList) {
        resObj.cmdb = cmdbList
        count++
        if (count === TASK_COUNT) {
          done && done()
        }
      })
    },
    getQueries () {
      let qs = []
      let query = 'topk(3,' + Metric.name.tenant.score_avg + ')'
      qs.push(query)
      return qs
    },
    /// 最终需要的数据
    /*
    此处的value即为te_score数据
    列表：list: [{info:{}, value:xx, metric1:xx, metric2:xx},{}]
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
        // 查询top3
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
