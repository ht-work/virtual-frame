<template>
  <div class="slide-container">
      <swiper class="swiper" :options="swiperOption">
        <swiper-slide v-for="item of list" :key="item.title">
          <DeviceMetricBar :config="item" />
        </swiper-slide>
      </swiper>
  </div>
</template>

<script>
import MixinTimer from '@/components/mixin/Mixin_Vue_Timer'
import MixinTooltip from '@/components/mixin/Mixin_Tooltip'
import { Swiper, SwiperSlide } from 'vue-awesome-swiper'
import 'swiper/css/swiper.css'

import DeviceMetricBar from './OV_Dev_Metric_Bar'

export default {
  name: 'LeftChart2',
  mixins: [MixinTimer, MixinTooltip],
  props: ['metricConfig'],
  components: {
    DeviceMetricBar,
    Swiper,
    SwiperSlide
  },
  computed: {
    list () {
      return this.metricConfig && this.metricConfig.list
    },
    swiperOption () {
      return this.metricConfig && this.metricConfig.swiperOption
    }
  }
}
</script>

<style lang="less">
.slide-container{
  > .swiper {
    height: 100%;
    width: 100%;
    .swiper-slide {
      display: flex;
      flex-direction: column;
      justify-content: center;
      /*align-items: center;  !*侧轴对齐方式，影响标题*!*/
      width: 90%;
      height: 100%;
      .chart-title{
        margin-bottom: 5px;
        display: flex;
        align-items: center;
      }
    }
  }
}

</style>
