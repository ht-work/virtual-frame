<template>
  <div class="ov-app-server-container">
    <div class="lc2-header special-header">
      <span>业务系统</span>
      <span class="text-more" @click='showMore'>更多...</span>
    </div>
    <MoreModal :show="showModal" @cancel="closeMore" />
    <div class="rank-container">
      <HealthChart />
    </div>
    <div class="usage-container">
      <BusyChart />
    </div>
  </div>
</template>

<script>
import MoreModal from './app/OV_App_More'
import HealthChart from './app/OV_App_1Health'
import BusyChart from './app/OV_App_2Busy'

export default {
  name: 'LeftChart2',
  // mixins: [Mixin, MixinColorCommon, MixinVueLifeCycle],
  components: {
    MoreModal,
    HealthChart,
    BusyChart
  },
  data () {
    let obj = {
      showModal: false
    }
    return obj
  },
  methods: {
    showMore () {
      this.showModal = true
    },
    closeMore () {
      this.showModal = false
    }
  }
}
</script>

<style lang="less">
.ov-app-server-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  .lc2-header{
    justify-content: space-between;
  }
  .rank-container{
    /*min-height: 160px;*/
    min-width: 200px;
    height: 60%;
    width: 100%;
  }
  .usage-container{
    height: 50%;
    margin-top: -30px;
    z-index: 2;
    /*display: inline-flex;*/
    /*justify-content: space-between;*/
    .usage-chart{
      width: 150%;
      transform-origin: top left;
      transform: scale(0.6, 0.6);
    }
  }
}
</style>
<style lang="less" scoped>
.busy-container{
  //width: 100%;
  text-align: center;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
