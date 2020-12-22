import Metric from '@/util/metric'
import MixinCommon from '../Mixin_OV_Common'

let mixin = {
  mixins: [MixinCommon],
  methods: {
    getSingleQuery () {
      let query = this.metrics[0] + '{type="' + this.type + '"}'
      return query
    },
    /// 最终需要的数据
    /*
    此处的value即为unbalance数据
    列表：list: [{info:{}, value:xx, cpu:xx, mem:xx},{}]
    */
    getMetric (cb) {
      let query = this.getSingleQuery()
      let self = this
      Metric.getSingleMetricValue(query, function (value) {
        let opt = self.getPieOption()
        self.fillOption(opt, value)
        cb && cb(opt)
      })
    },
    handleMetricData (data) {
      this.chartOpt = data
    },
    fillOption (opt, value) {
      let format = function () {
        return value + '%'
      }
      value = parseFloat(value)
      let data = [
        { value: value, name: '已使用' },
        { value: (100 - value), name: '空闲' }
      ]
      let series0 = opt && opt.series && opt.series[0]
      if (series0.label) {
        series0.label.formatter = format
      }
      series0.data = data
    },
    getPieOption () {
      let textColor = '#CCFFFFFF'
      let option = {
        color: ['#3FFFFE', '#282870'],
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        textStyle: {
          color: textColor
        },
        series: [
          {
            name: this.title,
            type: 'pie',
            radius: ['50%', '70%'],
            label: {
              show: true,
              // formatter: function(){ return '45%'},
              // fontSize: '30',
              // fontWeight: 'bold',
              position: 'center'
            },
            data: [
              // {value: 45, name: '已使用'},
              // {value: 55, name: '空闲'}
            ]
          }
        ]
      }
      return option
    },
    refresh () {
      this.loadData()
    }
  }
}

export default mixin
