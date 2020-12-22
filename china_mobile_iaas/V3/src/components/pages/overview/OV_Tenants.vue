<template>
  <div class="server-container">
    <div class="lc2-header special-header">
      <span>租户概况</span>
      <span class="text-more" @click='showMore'>更多...</span>
    </div>
    <MoreModal :show="showModal" @cancel="closeMore" />
    <div class="rank-container">
      <div class="item-header">
        <span>租户评分Top3</span>
        <span v-tooltip='getTips(tooltipKeys)' class="info-tooltip"></span>
      </div>
      <TenantTopN />
    </div>
  </div>
</template>

<script>
import MoreModal from './tenant/OV_Tenants_More'
import TenantTopN from './tenant/OV_Tenant_TopN'
import MixinTooltip from '@/components/mixin/Mixin_Tooltip'

export default {
  name: 'LeftChart2',
  mixins: [MixinTooltip],
  components: {
    MoreModal,
    TenantTopN
  },
  data () {
    let obj = {
      tooltipKeys: ['tenant.level', 'tenant.score', 'tenant.usageScore', 'tenant.assign', 'tenant.cpuScore', 'tenant.memScore', 'tenant.unbalance'],
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
    // ,
    // getRandomScore () {
    //   return this.getRandom(10, 100)
    // },
    // getBaseConfig () {
    //   let obj = {
    //     'A级': { min: 80, max: 100, color: this.getGreenColor() },
    //     'B级': { min: 60, max: 80, color: this.getYellowColor() },
    //     'C级': { min: 0, max: 60, color: this.getRedColor() }
    //   }
    //   return obj
    // },
    // getBaseData () {
    //   let items = [
    //     {
    //       name: '平台部',
    //       score: this.getRandomScore(),
    //       appCount: 25,
    //       mem: '10',
    //       cpuUsage: this.getRandomScore(),
    //       memUsage: this.getRandomScore()
    //     },
    //     {
    //       name: '运维部',
    //       score: this.getRandomScore(),
    //       appCount: 65,
    //       mem: '5',
    //       cpuUsage: this.getRandomScore(),
    //       memUsage: this.getRandomScore()
    //     },
    //     {
    //       name: '运营部',
    //       score: this.getRandomScore(),
    //       appCount: 76,
    //       mem: '20',
    //       cpuUsage: this.getRandomScore(),
    //       memUsage: this.getRandomScore()
    //     }
    //   ]
    //   return items
    // },
    // getColor (level) {
    //   let obj = this.getBaseConfig()
    //   return obj[level].color
    // },
    // getLevel (score) {
    //   let obj = this.getBaseConfig()
    //   let level = ''
    //   for (let k in obj) {
    //     if (obj[k].min <= score && score < obj[k].max) {
    //       level = k
    //       break
    //     }
    //   }
    //   level = level || 'A级'
    //   return level
    // },
    // getDataList () {
    //   let list = [
    //     {
    //       id: '1',
    //       name: '基础组',
    //       depart1: '技术部'
    //     },
    //     {
    //       id: '2',
    //       name: '平台组',
    //       depart1: '技术部'
    //     },
    //     {
    //       id: '3',
    //       name: 'IaaS组',
    //       depart1: '技术部'
    //     },
    //     {
    //       id: '4',
    //       name: 'PaaS组',
    //       depart1: '技术部'
    //     },
    //     {
    //       id: '5',
    //       name: 'SaaS组',
    //       depart1: '技术部'
    //     }
    //   ]
    //   return list
    // },
    // getDataObj () {
    //   let items = this.getBaseData()
    //   this.sortArray(items, 'score')
    //   for (let i in items) {
    //     let item = items[i]
    //     item.level = this.getLevel(item.score)
    //     item.color = this.getColor(item.level)
    //     item.assignRate = this.getRandomScore() + '%'
    //     item.cpuUsage = item.cpuUsage + '%'
    //     item.memUsage = item.memUsage + '%'
    //   }
    //   let obj = {
    //     showModal: false,
    //     items: items,
    //     dataList: this.getDataList()
    //   }
    //   return obj
    // },
    // refresh () {
    //   let obj = this.getDataObj()
    //   this.items = obj.items
    // }
  }
}
</script>

<style lang="less" scoped>
//@normalWidth: 30%;
//@biggerWidth: 40%;
.server-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  .lc2-header{
    justify-content: space-between;
  }

  .item-header{
    text-align: left;
    margin-bottom: 5px;
    margin-left: 10px;
    display: flex;
    align-items: center;
  }
  .score-container{
    display: inline-flex;
    align-items: center;
    .dv-digital-flop{
      width: 90px;
      height: 50px;
      display: inline-flex;
      margin-left: 10px;
    }
  }
}
</style>
<style lang="less">
#index {
  .server-container {
    .tenant-item {
      .dv-border-box-10 {
        .border-box-content {
          display: inline-block;
          padding: 5px;
        }
      }
    }
  }
}
</style>
