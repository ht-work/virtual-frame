<template>
  <div class="topN-container">
    <div class="lc2-header">
      <span>{{title}}</span>
    </div>
    <div class="topN-rows">
      <div class="topN-row item-border topN-header">
        <span class="item-value" v-for="v in headers">{{v}}</span>
      </div>
      <div class="topN-row item-border" v-for="item in items" :key="item.id">
        <span class="item-value">{{item.cmdb.owner_biz_system_bizSystem_name}}</span>
        <span class="item-value">{{item.value}}</span>
        <span class="item-value">{{item.cpu}}</span>
        <span class="item-value">{{item.mem}}</span>
      </div>
    </div>
  </div>
</template>

<script>

import Mixin from '@/components/mixin/Mixin'
import MixinTopN from './Mixin_Te_TopN'
import MixinColorCommon from '@/components/mixin/Mixin_Color_Common'
import Metric from '@/util/metric'

export default {
  name: 'CenterCmp',
  mixins: [Mixin, MixinColorCommon, MixinTopN],
  data () {
    let obj = {
      headers: ['名称', '不平衡度', 'CPU利用率（%）', '内存利用率（%）'],
      items: [],
      title: '不平衡度Top5业务系统',
      type: 'tenant',
      itemId: this.$route.query.id, // get from router
      metrics: [Metric.name.app.unbalance],
      // 根据metrics中的指标的topN的查询结果获取的Id列表再进行指标的查询
      idsQueryMetrics: [Metric.name.app.cpu, Metric.name.app.mem]
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
