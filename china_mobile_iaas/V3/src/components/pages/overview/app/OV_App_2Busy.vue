<template>
  <div class="topN-container">
    <div class="busy-container">
      <span>繁忙度Top5</span>
      <span v-tooltip='getTip("app.busy")' class="info-tooltip"></span>
    </div>
    <div class="topN-rows">
      <div class="topN-row item-border topN-header">
        <span class="item-value" v-for="v in headers">{{v}}</span>
      </div>
      <div class="topN-row item-border" v-for="item in items" :key="item.id">
        <span class="item-value">{{item.cmdb.name}}</span>
        <span class="item-value">{{item.value}}</span>
        <span class="item-value">{{item.resourceBusy && item.resourceBusy.VM}}</span>
        <span class="item-value">{{item.resourceBusy && item.resourceBusy.BM}}</span>
      </div>
    </div>
  </div>
</template>

<script>

import Mixin from '@/components/mixin/Mixin'
import MixinTopN from './Mixin_OV_App_Busy_TopN'
import MixinColorCommon from '@/components/mixin/Mixin_Color_Common'
import Metric from '@/util/metric'

export default {
  name: 'CenterCmp',
  mixins: [Mixin, MixinColorCommon, MixinTopN],
  data () {
    let obj = {
      headers: ['名称', '繁忙度', '云主机繁忙度', '裸金属繁忙度'],
      items: [],
      title: '繁忙度Top5',
      type: 'app',
      // itemId: this.$route.query.id, // get from router
      metrics: [Metric.name.app.busy],
      // 根据metrics中的指标的topN的查询结果获取的Id列表再进行指标的查询
      idsQueryMetrics: [Metric.name.app.resource_busy]
    }
    return obj
  }
}
</script>

<style lang="less" scoped>
.topN-rows {
  .topN-row {
    .item-value {
      width: 24%;
    }
  }
}
</style>
