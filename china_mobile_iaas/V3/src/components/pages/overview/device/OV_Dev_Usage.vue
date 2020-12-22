<template>
  <div class="usage-container">
<!--    <span style="margin-left: 10px;">资源利用率</span>-->
    <div class="usage-body">
      <div class="usage-item">
        <span class="usage-title">CPU利用率</span>
        <UsageChart :config="cpu" />
      </div>
      <div class="usage-item">
        <span class="usage-title">内存利用率</span>
        <UsageChart :config="mem" />
      </div>
    </div>
  </div>
</template>

<script>

import UsageChart from './OV_Dev_Usage_Pie'

export default {
  name: 'LeftChart2',
  components: {
    UsageChart
  },
  props: ['usage'],
  computed: {
    cpu () {
      return this.usage && this.usage.cpu
    },
    mem () {
      return this.usage && this.usage.mem
    }
  }
  // data () {
  //   let obj = {
  //     cpu: {
  //       type: 'VM',
  //       title: 'CPU利用率',
  //       metrics: [Metric.name.device.cpu_usage_avg]
  //     },
  //     mem: {
  //       type: 'VM',
  //       title: '内存利用率',
  //       metrics: [Metric.name.device.mem_usage_avg]
  //     }
  //   }
  //   return obj
  // }
}
</script>

<style lang="less" scoped>
.usage-container{
  width: 100%;
  height: 100%;
  position: relative;
  >span{
    position: absolute;
    left: 0;
    top: 5px;
  }
  .usage-body{
    /*margin-left: 60px;*/
    /*width: calc(~"100% - 60px");*/
    width: 100%;
    display: inline-flex;
    .usage-item{
      width: 50%;
      min-height: 80px;
      display: inline-flex;
      /*align-items: center;*/
      /*flex-direction: column;*/
      .usage-title{
        min-width: 70px;
        margin-left: 10px;
        margin-top:10px;
      }
    }
  }
}
</style>
