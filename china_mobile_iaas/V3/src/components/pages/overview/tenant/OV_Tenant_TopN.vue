<template>
  <div>
    <div v-for="(item,index) in items" :key="item.message" class="tenant-item" v-bind:style="{ color: item.color}"
    v-bind:class="{tenantItemBorder1:index===0,tenantItemBorder2:index===1,tenantItemBorder3:index===2}">
      <div class="rank-icon" v-bind:class="{rank1:index === 0, rank2: index === 1, rank3: index===2}"></div>
      <div class="detail-line-container">
        <div class="detail-line">
          <div class="detail-item biggest-width">
            <span>名称：</span>
            <span>{{item && item.cmdb && item.cmdb.name}}</span>
          </div>
          <div class="detail-item normal-width">
            <span>等级：</span>
            <span>{{item.level}}</span>
          </div>
        </div>
        <div class="detail-line">
          <div class="detail-item normal-width">
            <span>评分:</span>
            <span>{{item.value}}</span>
          </div>
          <div class="detail-item bigger-width">
            <span>资源使用率:</span>
            <span>{{item.metric.te_assign_ratio}}</span>
          </div>
          <div class="detail-item">
            <span>CPU评分:</span>
            <span>{{item.metric.te_cpu}}</span>
          </div>
        </div>
        <div class="detail-line">
          <div class="detail-item normal-width">
            <span>繁忙度:</span>
            <span>{{item.metric.te_busy}}</span>
          </div>
          <div class="detail-item bigger-width">
            <span>不平衡度:</span>
            <span>{{item.metric.te_unbalance}}</span>
          </div>
          <div class="detail-item">
            <span>内存评分:</span>
            <span>{{item.metric.te_mem}}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import Mixin from '@/components/mixin/Mixin'
import MixinTopN from './OV_Mixin_Te_TopN'
import MixinColorCommon from '@/components/mixin/Mixin_Color_Common'
import Metric from '@/util/metric'

export default {
  name: 'CenterCmp',
  mixins: [Mixin, MixinColorCommon, MixinTopN],
  data () {
    let obj = {
      // headers: ['名称', '不平衡度', 'CPU利用率', '内存利用率'],
      items: [],
      // title: '不平衡度Top5业务系统',
      type: 'tenant',
      // itemId: this.$route.query.id, // get from router
      metrics: [Metric.name.tenant.score],
      // 根据metrics中的指标的topN的查询结果获取的Id列表再进行指标的查询
      idsQueryMetrics: [Metric.name.tenant.usage_avg_replace, Metric.name.tenant.cpu_score_avg_replace,
        Metric.name.tenant.mem_score_avg_replace, Metric.name.tenant.busy_avg_replace, Metric.name.tenant.unbalance_avg_replace]
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
<style lang="less">
@normalWidth: 30%;
@biggerWidth: 40%;
.tenantItemBorder1{
  border-top: solid 1px #FFCD2A;
}
.tenantItemBorder2{
  border-top: solid 1px #F8FF8E;
}
.tenantItemBorder3{
  border-top: solid 1px #B6FFC6;
}
.tenant-item{
  /*border: solid 1px white;*/
  /*margin: 15px 0px;*/
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  .rank-icon{
    width: 20px;
    height: 20px;
    display: inline-block;
    margin: 0 5px;
  }
  .rank1{
    background-image: url("../../../../../public/static/img/tenant_1.svg");
  }
  .rank2{
    background-image: url("../../../../../public/static/img/tenant_2.svg");
  }
  .rank3{
    background-image: url("../../../../../public/static/img/tenant_3.svg");
  }
  .detail-line-container{
    width: calc(100% - 30px);
    display: inline-block;
  }
  .detail-line{
    /*margin-top: 5px;*/
    width: 100%;
    display: inline-flex;
    .detail-item{
      display: inline-block;
    }
    .normal-width{
      width: @normalWidth;
    }
    .bigger-width{
      width: @biggerWidth;
      /*margin-left: 5px;*/
    }
    .biggest-width{
      width: @normalWidth + @biggerWidth;
    }
  }
}
</style>
