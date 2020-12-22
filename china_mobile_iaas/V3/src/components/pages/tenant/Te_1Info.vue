<template>
  <Overview :items="list" />
</template>

<script>

import Overview from '@/components/common/Overview'

export default {
  name: 'Info',
  components: { Overview },
  props: ['info'],
  computed: {
    list () {
      // make list from info
      let list1 = [
        {
          key: '租户等级',
          value: this.info.metric.level
        },
        {
          key: '租户评分',
          value: this.info.metric.score
        },
        {
          key: '业务系统数量',
          value: this.info.cmdb.app_count
        },
        {
          key: '一级部门',
          value: this.info.cmdb.department1_orgName_name
        },
        {
          key: '所属资源池',
          value: this.info.cmdb.idcType_idc_name_name // '哈尔滨资源池'
        },
        {
          key: '云主机机数量（台）',
          value: this.info.cmdb.vm_amount // '600'
        },
        {
          key: '裸金属数量（台）',
          value: this.info.cmdb.bm_amount // '60'
        },
        {
          key: 'CPU总数（核）',
          value: Math.ceil(this.info.cmdb.vcpu_amount) // 20 * 512
        },
        {
          key: '内存总数（TB）',
          value: Math.ceil(this.info.cmdb.mem_amount) // 30 * 2
        }
      ]
      return list1
    }
  }
}
</script>

<style lang="less">

</style>
