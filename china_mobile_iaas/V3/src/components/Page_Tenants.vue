<template>
  <div class="index-container">

      <div class="main-header">
        <div class="mh-middle">{{ info && info.cmdb && info.cmdb.department2_orgName_name }}</div>
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
            <Unbalance />
          </div>
          <div class="right-chart chart-item">
            <Score />
          </div>
        </div>
      </div>
  </div>
</template>

<script>
import Operation from '@/components/common/Operation'
import Info from './pages/tenant/Te_1Info'
import Usage from './pages/tenant/Te_2Usage'
import Busy from './pages/tenant/Te_3Busy'
import TopN from './pages/tenant/Te_4TopN'
import Unbalance from './pages/tenant/Te_5Unbalance'
import Score from './pages/tenant/Te_6Score'

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
    Unbalance,
    Score
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
      BUS.emit(BUS.EVENTS.TENANT, data)
    },
    getInfo () {
      let self = this
      let TASK_COUNT = 2
      let count = 0
      let done = function () {
        let metric = {
          level: self.getTenantLevel(score),
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
      //let query = 'te_score{tenant="' + this.itemId + '"}'
      let query = 'avg(te_score{tenant="' + this.itemId + '"} <= 99999999) by (tenant)'
      Metric.getSingleMetricValue(query, function (v) {
        score = v
        count++
        if (count === TASK_COUNT) {
          done()
        }
      })
      CMDB.getTenantById(this.itemId, function (data) {
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
