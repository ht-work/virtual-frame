<template>
  <div class="topN-container">
    <div class="lc2-header"><span>{{title}}</span></div>
    <div class="topN-rows">
      <div class="topN-row item-border topN-header">
        <span class="item-value">{{headers[0]}}</span>
        <span class="item-value">{{headers[1]}}</span>
        <span class="item-value">{{headers[2]}}</span>
      </div>
      <div class="topN-row item-border" v-for="item in items" :key="item.id">
        <span class="item-value">{{item.cmdb.device_name}}</span>
        <span class="item-value">{{item.cmdb.ip}}</span>
        <span class="item-value">{{item.value}}</span>
      </div>
    </div>
  </div>
</template>

<script>

import Mixin from '@/components/mixin/Mixin'
import MixinAppTopN from './Mixin_App_TopN'
import MixinColorCommon from '@/components/mixin/Mixin_Color_Common'
import Metric from '@/util/metric'

export default {
  name: 'CenterCmp',
  mixins: [Mixin, MixinColorCommon, MixinAppTopN],
  data () {
    let obj = {
      headers: ['设备名称', 'IP地址', '健康度'],
      items: [],
      title: '健康度Bottom5设备',
      type: 'app',
      itemId: this.$route.query.id, // get from router
      metrics: [Metric.name.device.health]
    }
    return obj
  }
}
</script>

<style lang="less" scoped>
.topN-rows {
  .topN-row {
    .item-value {
      width: 32%;
    }
  }
}
</style>

<style lang="less">
.topN-rows{
  margin-top: 10px;
  .topN-row{
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 30px;
    padding: 0 20px;
    .item-value{
    }
  }
  .topN-row:nth-child(odd) {
    background: rgba(255,255,255,0.05);
  }
}

</style>
