import Metric from '@/util/metric'
import MixinCommon from '../Mixin_OV_Common'
import CMDB from '@/util/cmdb'

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
        item.id = item.metric.id
        //"metric":{"__name__":"device_unbalance","id":"id1","app":"App1","rp":"huchi1","tenant":"IT","type":"BM"}
        //"values":[ [时间,值],[时间，值] ]
        item.info = item.metric
        item.type = 'device'
        item.value = this.convertValue(item.value[1])
        delete item.metric
        resList.push(item)
      }
      return resList
    },
    formatCMDBData(entry){
      entry.id = entry.device_id
      entry.name = entry.device_name
      entry.app = entry.bizSystem
      entry.tenant = entry.department2_orgName_name
      entry.rp = entry.idcType_idc_name_name
    },
    // 合并cmdb数据和指标数据
    mergeMetricWithCMDB (resObj, metricData) {
      let cmdbObj = {}
      let cmdbData = resObj.cmdb
      for (let i = 0; i < cmdbData.length; i++) {
        this.formatCMDBData(cmdbData[i])
        cmdbObj[cmdbData[i].id] = cmdbData[i]
      }
      for (let j in metricData) {
        let entry = metricData[j]
        let id = entry.id
        entry.cmdb = cmdbObj[id]
      }
      return metricData
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

      CMDB.getDeviceByIds(ids, function (cmdbList) {
        resObj.cmdb = cmdbList
        count++
        if (count === TASK_COUNT) {
          done && done()
        }
      })
    },
    getSingleQuery () {
      let query = 'topk(3,' + this.metrics[0] + '{type="' + this.type + '"})'
      let metric = this.metrics[0]
      if (Metric.name.device.health === metric || Metric.name.device.ha === metric) {
        query = 'bottomk(3,' + this.metrics[0] + '{type="' + this.type + '"})'
      }
      return query
    },
    /// 最终需要的数据
    /*
    此处的value即为unbalance数据
    列表：list: [{info:{}, value:xx, cpu:xx, mem:xx},{}]
    */
    getMetric (cb) {
      let self = this
      let query = this.getSingleQuery()
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
    findItemWithParam (param) {
      console.log(param)
      let name = param[0].name
      let value = param[0].value
      let item = null
      for (let i = 0; i < this.metricData.length; i++){
        // 根据名称和值查找记录
        let entry = this.metricData[i]
        if (entry.cmdb && entry.cmdb.name === name && entry.value === value) {
          item = entry
          break
        }
      }
      return item
    },
    /*
    名称：name
      健康度：xx
      业务系统：xx
      所属部门：xx
      资源池：xx
     */
    buildTooltip (param) {
      console.log(param)
      let item = this.findItemWithParam(param)
      let html = item.cmdb.name
      html += '<br />' + this.title + '：' + item.value
      html += '<br />业务系统：' + item.cmdb.app
      html += '<br />所属部门：' + item.cmdb.tenant
      html += '<br />资源池：' + item.cmdb.rp
      return html
    },
    getBarOption () {
      let textColor = '#CCFFFFFF'
      let self = this
      let option = {
        color: ['#3FFFFE', '#282870'],
        title: {
          show: false
        },
        textStyle: {
          color: textColor
        },
        tooltip: {
          // CQC: tips
          // 添加到body元素之后，能够有效处理tooltip被遮挡的情况！
          renderMode: 'html',
          appendToBody: true,
          trigger: 'axis',
          formatter: function (param) {
            return self.buildTooltip(param)
          },
          axisPointer: {
            type: 'shadow'
          }
        },
        // 用于控制绘图区域距离canvas画布的空间
        grid: {
          top: '10px',
          bottom: '10px',
          left: '10px',
          right: '10px',
          containLabel: true
        },
        xAxis: {
          type: 'value'
        },
        yAxis: {
          type: 'category'
          // ,
          // data: ['巴西', '印尼', '美国']
        },
        series: [
          {
            barWidth: '50%',
            type: 'bar'
            // ,
            // data: [19325, 23438, 31000]
          }
        ]
      }
      return option
    },
    // 在获取了所有数据之后，构造option对象
    handleMetricData (data) {
      this.metricData = data
      let yAsix = []
      let seriesData = []
      for (let i = 0; i < data.length; i++) {
        let item = data[i]
        yAsix.push(item.cmdb.name)
        seriesData.push(item.value)
      }
      let opt = this.getBarOption()
      opt.yAxis.data = yAsix
      opt.series[0].data = seriesData
      this.chartOpt = opt
    },
    refresh () {
      this.loadData()
    }
  }
}

export default mixin
