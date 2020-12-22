<template>
  <div class="topN-container">
    <div class="lc2-header"><span>{{title}}</span></div>
    <div class="topN-rows">
      <div class="topN-row item-border topN-header">
        <span class="item-value" v-for="v in headers">{{v}}</span>
      </div>
      <div class="topN-row item-border" v-for="item in items" :key="item.id">
        <span class="item-value">{{item.cmdb.department2_orgName_name}}</span>
        <span class="item-value">{{Math.ceil(item.value)}}</span>
        <span class="item-value">{{Math.ceil(item.cpu)}}</span>
        <span class="item-value">{{Math.ceil(item.mem)}}</span>
      </div>
    </div>
  </div>
</template>

<script>

import Mixin from '@/components/mixin/Mixin'
import MixinTopN from './Mixin_Rp_TopN'
import MixinColorCommon from '@/components/mixin/Mixin_Color_Common'
import Metric from '@/util/metric'

export default {
  name: 'CenterCmp',
  mixins: [Mixin, MixinColorCommon, MixinTopN],
  data () {
    let obj = {
      headers: ['租户名称', '资源配额（台）', 'vCPU(核)', '内存(TB)'],
      items: [],
      title: '配额Top5租户',
      type: 'rp',
      itemId: this.$route.query.id, // get from router
      metrics: [Metric.name.tenant.quota_sum],
      // 根据metrics中的指标的topN的查询结果获取的Id列表再进行指标的查询
      idsQueryMetrics: [Metric.name.tenant.resource_quota]
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
