<template>
  <div id="resource-pool" class="index-container">

      <div class="main-header">
        <div class="mh-middle">{{ info && info.cmdb && info.cmdb.idcType_idc_name_name }}</div>
        <div class="mh-operation">
          <Operation @rangechange="onDateRangeChange"/>
        </div>
      </div>

      <div class="main-container">
        <div class="top-area part-area">
          <div class="left-chart chart-item">
            <Info :info="info"/>
          </div>
          <div class="middle-chart chart-item">
            <Usage />
          </div>
          <div class="right-chart chart-item">
            <Busy />
          </div>
        </div>
        <div class="bottom-area part-area">
          <div class="left-chart chart-item">
            <TopN />
          </div>
          <div class="middle-chart chart-item">
            <CPU />
          </div>
          <div class="right-chart chart-item">
            <Mem />
          </div>
        </div>
      </div>
  </div>
</template>

<script>
import Operation from '@/components/common/Operation'
import Info from './pages/rp/Rp_1Info'
import Usage from './pages/rp/Rp_2Assign'
import Busy from './pages/rp/Rp_3Busy'
import TopN from './pages/rp/Rp_4TopN'
import CPU from './pages/rp/Rp_5CPU'
import Mem from './pages/rp/Rp_6Mem'

import CMDB from '@/util/cmdb'
import Metric from '@/util/metric'
import BUS from '@/util/bus'

import MixinScoreLevel from '@/components/mixin/Mixin_Score_Level'

export default {
  name: 'DataView',
  mixins: [MixinScoreLevel],
  components: {
    Operation,
    Info,
    Usage,
    Busy,
    TopN,
    CPU,
    Mem
  },
  data () {
    return {
      itemId: this.$route.query.id, // get from router
      info: {
        cmdb: {},
        metric: {}
      }
    }
  },
  mounted () {
    this.getInfo()
  },
  methods: {
    onDateRangeChange (data) {
      console.log(data)
      BUS.emit(BUS.EVENTS.RP, data)
    },
    getInfo () {
      let self = this
      let TASK_COUNT = 2
      let count = 0
      let done = function () {
        let metric = {
          level: self.getRpLevel(score),
          score: score
        }
        let obj = {
          cmdb: cmdb,
          metric: metric
        }
        self.info = obj
      }
      let score
      let cmdb
      // 查询租户评分
      let query = 'rp_resource_score{rp="' + this.itemId + '"}'
      Metric.getSingleMetricValue(query, function (v) {
        score = v
        count++
        if (count === TASK_COUNT) {
          done()
        }
      })
      CMDB.getResourcePoolById(this.itemId, function (data) {
        cmdb = data
        count++
        if (count === TASK_COUNT) {
          done()
        }
      })
    }
  }
}
</script>
