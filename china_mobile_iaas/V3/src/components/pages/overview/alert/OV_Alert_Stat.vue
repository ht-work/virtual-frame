<template>
  <div class="chart-container">
    <PieChart :dom-id="chartId" :option="chartOpt" class="chart-area" />
  </div>
</template>

<script>
import MixinTimer from '@/components/mixin/Mixin_Vue_Timer'
import PieChart from '@/components/common/echarts/EchartsChart'
import config from '@/util/api_config'
import CMDB from '@/util/cmdb'

export default {
  name: 'LeftChart2',
  mixins: [MixinTimer],
  components: {
    PieChart
  },
  mounted () {
    this.initTimer(config.RefreshInterval)
    this.loadData && this.loadData()
  },
  data () {
    return {
      chartId: 'alert_stat',
      chartOpt: null
    }
  },
  methods: {
    getBaseOption () {
      let textColor = '#CCFFFFFF'
      let option = {
        color: ['#F86440', '#FFCD2A', '#298AFF', '#19D997'],
        textStyle: {
          color: textColor
        },
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        // legend: {
        //   // orient: 'vertical',
        //   // left: 10
        //   // ,
        //   // data: ['直接访问', '邮件营销', '联盟广告', '视频广告', '搜索引擎']
        // },
        series: [
          {
            name: '告警统计',
            type: 'pie',
            radius: ['30%', '50%'],
            // avoidLabelOverlap: false,
            label: {
              show: true,
              // distanceToLabelLine: 10,
              position: 'outside'
            },
            // emphasis: {
            //   label: {
            //     show: true,
            //     // fontSize: '30',
            //     fontWeight: 'bold'
            //   }
            // },
            labelLine: {
              show: true,
              length: 5,
              smooth: true,
              length2: 5
            },
            data: [
              // {value: 335, name: '直接访问'},
              // {value: 310, name: '邮件营销'},
              // {value: 234, name: '联盟广告'},
              // {value: 135, name: '视频广告'},
              // {value: 1548, name: '搜索引擎'}
            ]
          }
        ]
      }
      return option
    },
    parseResponse (resObj) {
      let legends = ['紧急', '重要', '次要', '一般']
      let data = [resObj['2'] || 0, resObj['3'] || 0, resObj['4'] || 0, resObj['5'] || 0]
      let list = [
        { name: legends[0], value: data[0] },
        { name: legends[1], value: data[1] },
        { name: legends[2], value: data[2] },
        { name: legends[3], value: data[3] }
      ]
      let obj = {
        list: list,
        legends: legends
      }
      return obj
    },
    loadData () {
      let self = this
      CMDB.getStatForAlert(function (data) {
        if (data) {
          let opt = self.getBaseOption()
          let obj = self.parseResponse(data)
          // opt.legend.data = obj.legends
          opt.series[0].data = obj.list
          self.chartOpt = opt
        }
      })
    }
  }
}
</script>

<style lang="less" scoped>
.chart-container{
  width: 100%;
  height: 100%;
  .chart-area{
    height: 100%;
    min-height: 160px;
  }
}
</style>
