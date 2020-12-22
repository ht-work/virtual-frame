import Metric from '@/util/metric'
import MixinCommon from '../Mixin_OV_Common'
import CMDB from '@/util/cmdb'

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
      //过滤出15条记录查询cmdb数据，查询出的数据取前5个有数据的记录
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

      let result = [];
      //取前5个
      let count = 0;
      for (let j in metricData) {
        if(count >= 5){
          break
        }
        let entry = metricData[j]
        let id = entry.id
        if(typeof(cmdbObj[id]) == 'undefined'){
          continue;
        }
        entry.cmdb = cmdbObj[id]
        result.push(entry)
        count++
      }
      return result
    },

    buildTopNData (ids, baseMetricList, cb) {
      let count = 0
      let resObj = {}
      let TASK_COUNT = 1
      let self = this

      let done = function () {
        let newList = self.mergeMetricWithCMDB(resObj, baseMetricList)
        cb && cb(newList)
      }

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
      // 获取前25条记录，最后再过滤
      let query = 'bottomk(25,' + this.metrics[0] + ')'
      let queries = [query]
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
        // 查询topk数据
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
    getBarOption () {
      let textColor = '#CCFFFFFF'
      let option = {
        // title: {
        //   text: this.chartConfig.title,
        //   left: 'center',
        //   top: '10px',
        //   textStyle: {
        //     color: textColor
        //   }
        // },
        textStyle: {
          color: textColor
        },
        tooltip: {
          trigger: 'axis'
        },
        // 用于控制绘图区域距离canvas画布的空间
        grid: {
          top: '20px',
          bottom: '30px',
          left: '10px',
          right: '10px',
          containLabel: true
        },
        xAxis: {
          type: 'category'
          // ,
          // boundaryGap: false
          // data: dataObj.times    // 变量
        },
        yAxis: {
          type: 'value'
        }
        // ,
        // series: this.getSeries(dataObj) // 变量
      }
      return option
    },
    // 在获取了所有数据之后，构造option对象
    handleMetricData (data) {
      let xAsix = []
      let seriesData = []
      for (let i = 0; i < data.length; i++) {
        let item = data[i]
        if(typeof(item.cmdb) != 'undefined' && item.cmdb != null){
          xAsix.push(item.cmdb.name)
          seriesData.push(item.value)
        }else{
          console.log("find no cmdb data.");
          console.log(item);
        }
      }
      let opt = this.getBarOption()
      opt.xAxis.data = xAsix
      opt.series = [{
        data: seriesData,
        barWidth: '50%',
        type: 'bar'
      }]
      this.chartOpt = opt
      //console.log("[#######]" + JSON.stringify(this.chartOpt))
    },
    refresh () {
      this.loadData()
    }
  }
}

export default mixin
