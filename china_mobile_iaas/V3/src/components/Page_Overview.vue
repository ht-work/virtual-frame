<template>
  <div id="index" class="OV-container">
<!--    <dv-full-screen-container>-->

      <div class="main-header">
        <div class="mh-middle">中国移动IaaS平台</div>
      </div>

    <div class="main-container">

        <div class="left-part common-space">
          <div class="left-chart-item-top left-item">
            <Assert-Chart />
          </div>
          <div class="left-chart-item-middle left-item">
            <Tenants />
          </div>
          <div class="left-chart-item-bottom left-item">
            <App-System />
          </div>
        </div>

        <div class="middle-part common-space" style="">
          <div class="middle-top">
              <Core-Chart />
          </div>
          <div class="middle-bottom">
              <Bottom-Charts />
          </div>
        </div>

        <RightCharts />
    </div>
  </div>
</template>

<script>
import AssertChart from '@/components/pages/overview/OV_Overview'
import Tenants from '@/components/pages/overview/OV_Tenants'
import AppSystem from '@/components/pages/overview/OV_App'

import CoreChart from '@/components/pages/overview/OV_Core'
import BottomCharts from '@/components/pages/overview/OV_BottomCharts'

import RightCharts from '@/components/pages/overview/OV_RightCharts'

export default {
  name: 'DataView',
  components: {
    AssertChart,
    Tenants,
    AppSystem,
    CoreChart,
    // CloudResource,
    // VMResource,
    RightCharts,
    BottomCharts
  }
}
</script>


<style lang="less">
@import "./common/MoreDialog.less";
</style>

<style lang="less">
@overviewItemHeight: 22px;
@overviewHeight: @overviewItemHeight * 8 + 30px;
.OV-container {
  width: 100%;
  height: 100%;
  background-color: #10103A;
  color: #fff;

  .main-container {
    height: calc(~"100% - 60px");
    display: flex;
    justify-content: center;
  }

  .left-part {
    width: 25%;
    min-width: 240px;
    .left-chart-item-top{
    }
    .left-chart-item-middle{
    }
    .left-chart-item-bottom{
    }
  }
  .left-item{
    border: 1px solid rgba(41, 138, 255, 0.4);
    margin-bottom: 10px;
  }
  .middle-part {
    width: 45%;
    min-width: 440px;
    /*height: 100%;*/
    .middle-top {
      width: 100%;
      height: 50%;
    }
    .middle-bottom {
      margin-top: 10px;
      width: 100%;
      /*height: 25%;*/
    }
  }
  .common-space{
    padding: 0 5px;
  }
  .right-part {
    width: 25%;
    min-width: 240px;
    display: flex;
    flex-direction: column;
    .right-chart-item{
      /*height: 25%;*/
      margin-bottom: 10px;
      border: 1px solid rgba(41, 138, 255, 0.4);
      /*border: solid 1px white;*/
    }
  }
}
</style>
