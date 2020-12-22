<template>
  <div class="bottom-charts">
    <div class="bc-chart-item bc-chart-item-left">
      <div class="lc2-header header-align">告警统计</div>
      <AlertStat />
    </div>

<!--    <dv-decoration-2 class="decoration-2" :reverse="true" style="width:5px;"/>-->

    <div class="bc-chart-item bc-chart-item-right">
      <div class="lc2-header header-align"><span>最新告警</span></div>
      <AlertList/>
    </div>
  </div>
</template>

<script>
import AlertStat from './alert/OV_Alert_Stat'
import AlertList from './alert/OV_Alert_List'
import Mixin from '@/components/mixin/Mixin'

export default {
  name: 'BottomCharts',
  mixins: [Mixin],
  components: {
    AlertStat,
    AlertList
  }
}
</script>

<style lang="less" scoped>
.bottom-charts {
  width: 100%;
  height: 100%;
  display: flex;
  position: relative;

  .bc-chart-item-left {
    width: 30%;
    min-width: 130px;
    margin-right: 10px;
  }

  .bc-chart-item-right {
    width: 70%;
    min-width: 300px;
    overflow: hidden;
    /*padding-left: 20px;*/
  }

  .bc-chart-item {
    height: 100%;
    /*padding-left: 10px;*/
    border: 1px solid rgba(41, 138, 255, 0.4);
    min-height: 205px;
  }

  .bcci-header {
    height: 30px;
    line-height: 30px;
  }

  .header-align {
    text-align: left;
  }
}
</style>
