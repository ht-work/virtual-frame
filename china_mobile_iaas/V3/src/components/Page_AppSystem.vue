<template>
  <div class="index-container">

      <div class="main-header">
        <div class="mh-middle">{{ info && info.cmdb && info.cmdb.biz_sys_name }}</div>
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
            <Unbalance />
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
            <Health />
          </div>
          <div class="right-chart chart-item">
            <Ha />
          </div>
        </div>
      </div>
  </div>
</template>

<script>
import Operation from '@/components/common/Operation'
import Info from '@/components/pages/app/App_Info'
import Usage from '@/components/pages/app/App_Usage'
import Unbalance from '@/components/pages/app/App_Unbalance'
import Busy from '@/components/pages/app/App_Busy'
import TopN from '@/components/pages/app/App_TopN'
import Health from '@/components/pages/app/App_Health'
import Ha from '@/components/pages/app/App_Ha'

import CMDB from '@/util/cmdb'
import BUS from '@/util/bus'

export default {
  name: 'DataView',
  components: {
    Operation,
    Info,
    Usage,
    Unbalance,
    Busy,
    TopN,
    Health,
    Ha
  },
  data () {
    return {
      itemId: this.$route.query.id, // get from router
      info: {
        cmdb: {}
      }
    }
  },
  mounted () {
    this.getInfo()
  },
  methods: {
    onDateRangeChange (data) {
      console.log(data)
      BUS.emit(BUS.EVENTS.APP, data)
    },
    getInfo () {
      let self = this
      CMDB.getAppById(this.itemId, function (data) {
        self.info = {
          cmdb: data
        }
      })
    }
  }
}
</script>

<style lang="less">
.index-container {
  width: 100%;
  height: 100%;
  //background-color: #030409;
  color: #fff;

  .main-container {
    height: calc(~"100% - 80px");
    flex-direction: column;
    .part-area{
      display: flex;
      justify-content: center;
    }
    .chart-item{
      min-width: 30%;
      margin: 5px 5px;
      background: rgba(32,32,86,0.20);
      border: 1px solid rgba(41,138,255,0.40);
      /*padding-top: 20px;*/
      .chart-title{
        text-align: center;
      }
    }
    .top-area{
      height: 35%;
      min-height: 250px;
    }
    .bottom-area{
      height: 25%;
      min-height: 230px;
    }
  }
}
</style>
