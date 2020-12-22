import Metric from '@/util/metric'
import MixinCommon from './Mixin_Rp_Common'
import MixinMetric from '@/components/mixin/Mixin_Metric'
import BUS from '@/util/bus'
import moment from 'moment'

let mixin = {
  mixins: [MixinCommon, MixinMetric],
  methods: {
    specialInit: function () {
      let self = this
      BUS.on(BUS.EVENTS.RP, self.handleDateRangeChange)
    },
    handleDateRangeChange (data) {
      console.log('receive data range change: ' + this.title)
      console.log(data)
      this.dateRangeConfig = data
      this.loadData()
    },
    handleSpecialMetric (metricObj) {
      // // 业务系统繁忙度没有type字段，手工增加该字段，用于展示总体繁忙度
      // let name = metricObj && metricObj.__name__
      // let knownMetrics = ['te_busy', 'te_unbalance', 'te_score']
      // if (knownMetrics.indexOf(name) !== -1) {
      //   metricObj.type = 'WHOLE'
      // }
    },
    /*
返回以下结构对象：
{
  VM:[]
  BM:[]
  vCPU:[]
  mem:[]
  time:[]
  info: {}
}
 */
    handleRangeResponse (list) {
      let obj = {}
      let info = null
      for (let i in list) {
        let item = list[i]
        if (this.handleSpecialMetric) {
          this.handleSpecialMetric(item.metric)
        }
        let type = item.metric.type
        // "metric":{"__name__":"app_resource_assign_ratio","app":"App1","rp":"huchi1","tenant":"IT","type":"BM"}
        // "values":[ [时间,值],[时间，值] ]
        if (!info) {
          info = item.metric
          delete info.type
          obj.info = info
        }
        for (let j in item.values) {
          let vItem = item.values[j]
          vItem[1] = this.convertValue(vItem[1])
          vItem[0] = vItem[0] * 1000
        }
        obj[type] = item.values
      }
      return obj
    },
    getRangeQueryParam () {
      let param = Metric.getDefaultRangeQueryParam()
      let conf = this.dateRangeConfig
      if (conf && conf.customMode && conf.dataRange &&
        conf.dataRange.startDate && conf.dataRange.endDate) {
        param = {
          start: Metric.getTime(conf.dataRange.startDate),
          end: Metric.getTime(conf.dataRange.endDate),
          step: this.getStep(conf.dataRange.startDate, conf.dataRange.endDate)
        }
      }
      // console.log(param)
      return param
    },
    getMetric (cb) {
      let self = this
      let queries = this.getQueries()
      //console.log("start to query metric for rp.")
      //console.log(JSON.stringify(queries))
      let TASK_COUNT = queries.length
      let count = 0
      let resList = []
      let done = function () {
        let obj = self.handleRangeResponse(resList)
        cb && cb(obj)
      }
      let func = function (query, callback) {
        let param = self.getRangeQueryParam()
        Metric.queryRange(query, param, function (data) {
          // console.log('before resList: ' + JSON.stringify(resList))
          resList = resList.concat(data)
          // console.log('after resList: ' + JSON.stringify(resList))
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
    getTypeNameMap () {
      let obj = {
        'KVM宿主机': 'PM',
        '裸金属': 'BM',
        '云主机': 'VM',
        'vCPU': 'VCPU',
        '内存': 'MEM'
      }
      return obj
    },
    getSeries (dataObj) {
      let legends = this.chartConfig.legends
      let nameMap = this.getTypeNameMap()
      let series = []
      for (let i in legends) {
        let legendName = legends[i]
        let item = {
          name: legendName,
          type: 'line',
          smooth: true,
          data: dataObj[ nameMap[legendName] ]
        }
        series.push(item)
      }
      return series
    },
    getLineOption (dataObj) {
      let textColor = '#9898AB'
      let lineColor = '#9898AB'
      let option = {
        color: ['#3EFCFC', '#FFCD2A', '#298AFF', '#FF424D'],
        textStyle: {
          color: textColor
        },
        tooltip: {
          trigger: 'axis'
        },
        // 用于控制绘图区域距离canvas画布的空间
        grid: {
          top: '50px',
          bottom: '30px',
          left: '10px',
          right: '40px',
          containLabel: true
        },
        legend: {
          show: !this.chartConfig.hideLegend,
          data: this.chartConfig.legends,
          textStyle: {
            color: textColor
          },
          bottom: '5px'
        },
        xAxis: {
          name: '日期',
          type: 'time',
          splitLine: {
            // 垂直网格线
            show: false
          },
          boundaryGap: false,
          // 此处可以不指定横轴，直接在数据层面进行处理，即 [时间,值]
          // prometheus返回数据能够直接作为time类型数据展示
          /*
          参考：https://stackoverflow.com/questions/51861846/how-to-make-echart-x-axis-type-time-to-display-a-time-period-for-one-day
          原文：And if you use type=time, you don't have to set data of Axis, just set series datas,
          axis range will auto set by given time, like:
           */
          axisLabel: {
            formatter: function (value) {
              // return new Date(value).toLocaleDateString()
              return moment(value).format('MM/DD');
            }
          }
          // data: dataObj.times    // 变量
        },
        yAxis: {
          type: 'value',
          name: this.chartConfig && this.chartConfig.yTitle,
          splitLine: {
            // 水平网格线
            show: true,
            lineStyle: {
              color: lineColor
            }
          },
          axisLabel: {
            formatter: '{value} %' // 变量
          }
        },
        series: this.getSeries(dataObj) // 变量
      }
      return option
    },
    handleMetricData (data) {
      let opt = this.getLineOption(data)
      this.chartOpt = opt
    },
    refresh () {
      // 在用户手工选择时间区间时，定时器到达时不做任何事情
      if (this.dateRangeConfig && this.dateRangeConfig.customMode) {
        console.log('customMode enabled, and do nonthing when timer reaches')
      } else {
        console.log('timer reaches and load data again')
        this.loadData()
      }
    }
  }
}

export default mixin
